from typing import List, Tuple

import attr


@attr.s(auto_attribs=True, frozen=True)
class Row:
    img_name: str
    noses: List[Tuple[int, int]]
    include_to_tests: bool = True


SAMPLE_IMAGES = [
    Row('000_5.jpg', [(219, 105), (300, 252), (392, 220), (469, 309), (600, 294)]),
    Row('001_A.jpg', [(2109, 2261)]),
    Row('002_A.jpg', [(2146, 2424)]),
    Row('003_A.jpg', [(3210, 1382)]),
    Row('004_A.jpg', [(1312, 1969)]),
    Row('005_A.jpg', [(2092, 2871)]),
    Row('006_A.jpg', [(1864, 3041)]),
    Row('007_B.jpg', [(210, 292)]),
    Row('008_B.jpg', [(225, 256)]),
    Row('009_C.jpg', [(166, 236)]),
    Row('010_2.jpg', [(354, 232), (505, 258)]),
    Row('011_3.jpg', [(295, 266), (484, 245), (385, 216)]),
    Row('012_4.jpg', [(208, 205), (318, 241), (454, 228), (641, 240)]),
    Row('013_4.jpg', [(254, 205), (343, 184), (423, 200), (512, 182)]),
    Row('014_5.jpg', [(95, 283), (207, 262), (407, 175), (605, 270), (691, 305)]),
    Row('015_6.jpg', [(164, 229), (269, 269), (352, 282), (453, 269), (557, 263), (635, 250)]),
    Row('016_8.jpg', [(194, 277), (262, 169), (260, 292), (357, 278), (440, 213), (459, 287), (521, 161),
                      (691, 201)]),
    Row('017_0.jpg', []),
    Row('018_2.jpg', [(221, 142), (147, 161)], include_to_tests=False),
    Row('019_1.jpg', [(324, 179)], include_to_tests=False),
]
name_2_annotation = {r.img_name: r.noses for r in SAMPLE_IMAGES}