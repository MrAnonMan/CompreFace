import logging
from http import HTTPStatus

from flask import Response
from flask.json import jsonify
from werkzeug.exceptions import BadRequest

from src.services.async_task_manager.training_task_manager import AsyncTaskManager
from src.services.classifier.logistic_classifier import LogisticClassifier
from src.services.dto.face_prediction import FacePrediction
from src.services.facescan.backend.facescan_backend import FacescanBackend
from src.services.flaskext.authentication import needs_authentication
from src.services.flaskext.auto_retraining import needs_retrain
from src.services.flaskext.constants import API_KEY_HEADER, GetParameter, ARG
from src.services.flaskext.file_attachments import needs_attached_file
from src.services.flaskext.parse_request_arg import parse_request_bool_arg
from src.services.storage.face import Face
from src.services.storage.mongo_storage import MongoStorage
from src.services.utils.nputils import read_img
from src.cache import get_storage, get_scanner, get_training_task_manager


def endpoints(app):
    @app.route('/status')
    def get_status():
        return jsonify(status="OK")

    @app.route('/faces')
    @needs_authentication
    def list_faces():
        from flask import request
        api_key = request.headers[API_KEY_HEADER]

        storage: MongoStorage = get_storage()
        face_names = storage.get_face_names(api_key)

        return jsonify(names=face_names)

    @app.route('/faces/<face_name>', methods=['POST'])
    @needs_authentication
    @needs_attached_file
    @needs_retrain
    def add_face(face_name):
        from flask import request
        img = read_img(request.files['file'])
        api_key = request.headers[API_KEY_HEADER]
        detection_threshold_c = _get_detection_threshold_c(request)
        scanner: FacescanBackend = get_scanner()
        storage: MongoStorage = get_storage()

        face = scanner.scan_one(img, detection_threshold_c)
        storage.add_face(api_key,
                         Face(name=face_name, raw_img=img, face_img=face.img, embedding=face.embedding),
                         emb_calc_version=scanner.ID)

        return Response(status=HTTPStatus.CREATED)

    @app.route('/faces/<face_name>', methods=['DELETE'])
    @needs_authentication
    @needs_retrain
    def remove_face(face_name):
        from flask import request
        api_key = request.headers[API_KEY_HEADER]
        storage: MongoStorage = get_storage()

        storage.remove_face(api_key, face_name)

        return Response(status=HTTPStatus.NO_CONTENT)

    @app.route('/retrain', methods=['GET'])
    @needs_authentication
    def retrain_model_status():
        from flask import request
        api_key = request.headers[API_KEY_HEADER]
        task_manager: AsyncTaskManager = get_training_task_manager()

        it_is_training = task_manager.is_training(api_key)

        return Response(status=HTTPStatus.ACCEPTED if it_is_training else HTTPStatus.OK)

    @app.route('/retrain', methods=['POST'])
    @needs_authentication
    def retrain_model_start():
        from flask import request
        api_key = request.headers[API_KEY_HEADER]
        force_start = parse_request_bool_arg(name=GetParameter.FORCE, default=False, request=request)
        task_manager: AsyncTaskManager = get_training_task_manager()

        task_manager.start_training(api_key, force_start)

        return Response(status=HTTPStatus.ACCEPTED)

    @app.route('/retrain', methods=['DELETE'])
    @needs_authentication
    def retrain_model_abort():
        from flask import request
        api_key = request.headers[API_KEY_HEADER]
        task_manager: AsyncTaskManager = get_training_task_manager()

        task_manager.abort_training(api_key)

        return Response(status=HTTPStatus.NO_CONTENT)

    @app.route('/recognize', methods=['POST'])
    @needs_authentication
    @needs_attached_file
    def recognize_faces():
        from flask import request
        img = read_img(request.files['file'])
        detection_threshold_c = _get_detection_threshold_c(request)
        return_limit = _get_return_limit(request)
        scanner: FacescanBackend = get_scanner()
        storage: MongoStorage = get_storage()
        api_key = request.headers[API_KEY_HEADER]
        classifier = storage.get_embedding_classifier(api_key, LogisticClassifier.CURRENT_VERSION, scanner.ID)

        predictions = []
        for face in scanner.scan(img, return_limit, detection_threshold_c):
            prediction = classifier.predict(face.embedding, scanner.ID)
            face_prediction = FacePrediction(prediction.face_name, prediction.probability, face.box)
            predictions.append(face_prediction)

        return jsonify(result=predictions)


def _get_detection_threshold_c(request):
    detection_threshold_c = request.values.get(ARG.DET_PROB_THRESHOLD)
    return float(detection_threshold_c) if detection_threshold_c is not None else None


def _get_return_limit(request):
    limit = request.values.get(ARG.LIMIT)
    if limit is None:
        return limit

    try:
        limit = int(limit)
    except ValueError as e:
        raise BadRequest('Limit format is invalid (limit >= 0)') from e

    if not (limit >= 0):
        raise BadRequest('Limit value is invalid (limit >= 0)')

    return limit
