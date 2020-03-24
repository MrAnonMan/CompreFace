import logging
from enum import auto

import gridfs
from pymongo import MongoClient
from sklearn.linear_model import LogisticRegression
from strenum import StrEnum

from src.exceptions import NoTrainedEmbeddingClassifierFound
from src.services.classifier.logistic_classifier import LogisticClassifier
from src.services.facescan.backend.facescan_backend import FacescanBackend
from src.services.storage.face import Face, FaceNameEmbedding
from src.services.storage.mongo_fileio import save_file_to_mongo, get_file_from_mongo
from src.services.utils.pyutils import serialize, deserialize
from src.cache import get_scanner

MONGO_EFRS_DATABASE_NAME = "efrs_db"


class CollectionName(StrEnum):
    FACES = auto()
    CLASSIFIERS = auto()
    FILES = auto()


class MongoStorage:
    def __init__(self, mongo_host: str, mongo_port: int):
        self._mongo_host = mongo_host
        self._mongo_port = mongo_port
        self._mongo_client = MongoClient(host=self._mongo_host, port=self._mongo_port)
        db = self._mongo_client[MONGO_EFRS_DATABASE_NAME]
        self._faces_collection = db[CollectionName.FACES]
        self._faces_fs = gridfs.GridFS(db, CollectionName.FACES)
        self._classifiers_collection = db[CollectionName.CLASSIFIERS]
        self._classifiers_fs = gridfs.GridFS(db, CollectionName.CLASSIFIERS)
        self._files_fs = gridfs.GridFS(db, CollectionName.FILES)

    def check_connection(self):
        logging.debug(f"Mongo database connection: '{self._mongo_host}:{self._mongo_port}'")
        self._mongo_client.server_info()

    def add_face(self, api_key: str, face: Face, emb_calc_version: str):
        self._faces_collection.insert_one({
            "face_name": face.name,
            "embeddings": [
                {
                    "array": face.embedding.tolist(),
                    "calculator_version": emb_calc_version
                }
            ],
            "raw_img_fs_id": self._faces_fs.put(serialize(face.raw_img)),
            "face_img_fs_id": self._faces_fs.put(serialize(face.face_img)),
            "api_key": api_key
        })

    def _get_or_create_embedding(self, face_document, emb_calc_version, raw_img, api_key, face_name):
        found_embeddings = [emb for emb in face_document['embeddings'] if
                            emb['calculator_version'] == emb_calc_version]
        if found_embeddings:
            return found_embeddings[0]['array']

        logging.warning("Embedding was not found for a face in the database, calculating")
        scanner: FacescanBackend = get_scanner()
        assert scanner.ID == emb_calc_version
        embedding = scanner.scan_one(raw_img).embedding
        self._faces_collection.find_one_and_update(
            filter={"api_key": api_key, "face_name": face_name},
            update={'$push': {"embeddings": {"array": embedding.tolist(), "calculator_version": emb_calc_version}}})
        return embedding

    def get_faces(self, api_key: str, emb_calc_version: str):
        faces = []
        for face_document in self._faces_collection.find({"api_key": api_key}):
            face_name = face_document['face_name']
            raw_img = deserialize(self._faces_fs.get(face_document['raw_img_fs_id']).read()),
            face_img = deserialize(self._faces_fs.get(face_document['face_img_fs_id']).read())
            embedding = self._get_or_create_embedding(face_document, emb_calc_version, raw_img, api_key, face_name)
            faces.append(Face(name=face_name, embedding=embedding, raw_img=raw_img, face_img=face_img))
        return faces

    def remove_face(self, api_key: str, face_name: str):
        raw_imgs = self._faces_collection.find(filter={"face_name": face_name, "api_key": api_key},
                                               projection={"raw_img_fs_id"}).distinct("raw_img_fs_id")
        for raw_img in raw_imgs:
            self._faces_fs.delete(raw_img)
        face_imgs = self._faces_collection.find(filter={"face_name": face_name, "api_key": api_key},
                                                projection={"face_img_fs_id"}).distinct("face_img_fs_id")
        for face_img in face_imgs:
            self._faces_fs.delete(face_img)

        self._faces_collection.delete_many({'face_name': face_name, 'api_key': api_key})

    def get_face_names(self, api_key: str):
        return self._faces_collection.find(filter={"api_key": api_key},
                                           projection={"face_name": 1}).distinct("face_name")

    def get_face_embeddings(self, api_key: str, emb_calc_version: str):
        face_embeddings = []
        for face_document in self._faces_collection.find({"api_key": api_key}):
            face_name = face_document['face_name']
            raw_img = deserialize(self._faces_fs.get(face_document['raw_img_fs_id']).read())
            embedding = self._get_or_create_embedding(face_document, emb_calc_version, raw_img, api_key, face_name)
            face_embeddings.append(FaceNameEmbedding(name=face_name, embedding=embedding))
        return face_embeddings

    def save_embedding_classifier(self, api_key: str, embedding_classifier: LogisticClassifier):
        self._classifiers_collection.update({
            'version': embedding_classifier.version,
            'embedding_calculator_version': embedding_classifier.emb_calc_version,
            "api_key": api_key
        }, {
            'version': embedding_classifier.version,
            'embedding_calculator_version': embedding_classifier.emb_calc_version,
            "api_key": api_key,
            "class_2_face_name": {str(k): v for k, v in embedding_classifier.class_2_face_name.items()},
            "classifier_fs_id": self._classifiers_fs.put(serialize(embedding_classifier.model))
        }, upsert=True)

    def get_embedding_classifier(self, api_key, version, emb_calc_version):
        document = self._classifiers_collection.find_one({
            'version': version,
            'embedding_calculator_version': emb_calc_version,
            "api_key": api_key
        })
        if document is None:
            raise NoTrainedEmbeddingClassifierFound

        # noinspection PyTypeChecker
        model: LogisticRegression = deserialize(self._classifiers_fs.get(document['classifier_fs_id']).read())
        class_2_face_name = {int(k): v for k, v in document['class_2_face_name'].items()}
        return LogisticClassifier(model, class_2_face_name, emb_calc_version, version)

    def delete_embedding_classifiers(self, api_key):
        face_query = self._classifiers_collection.find(filter={"api_key": api_key}, projection={"classifier_fs_id"})
        for classifier_file in face_query.distinct("classifier_fs_id"):
            self._classifiers_fs.delete(classifier_file)
        self._classifiers_collection.delete_many({'api_key': api_key})

    def get_api_keys(self):
        return self._faces_collection.find(projection=["api_key"]).distinct("api_key")

    def save_file(self, filename, bytes_data):
        save_file_to_mongo(self._files_fs, filename, bytes_data)

    def get_file(self, filename):
        return get_file_from_mongo(self._files_fs, filename)
