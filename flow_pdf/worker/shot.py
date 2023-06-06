from .common import PageWorker, Block, Range, get_min_bounding_rect, rectangle_relation, RectRelation
from .common import (
    DocInputParams,
    PageInputParams,
    DocOutputParams,
    PageOutputParams,
    LocalPageOutputParams,
)


from dataclasses import dataclass


@dataclass
class DocInParams(DocInputParams):
    big_text_columns: list[Range]

    core_y: Range


@dataclass
class PageInParams(PageInputParams):
    big_blocks: list[list]  # column -> block
    raw_dict: dict
    drawings: list


@dataclass
class DocOutParams(DocOutputParams):
    pass


@dataclass
class PageOutParams(PageOutputParams):
    shot_rects: list[list]  # column -> block


@dataclass
class LocalPageOutParams(LocalPageOutputParams):
    pass





class ShotWorker(PageWorker):
    def run_page(  # type: ignore[override]
        self, page_index: int, doc_in: DocInParams, page_in: PageInParams
    ) -> tuple[PageOutParams, LocalPageOutParams]:
        column_shots: list[list[list[tuple[float, float, float, float]]]] = []

        # shot between big blocks
        for i, column in enumerate(doc_in.big_text_columns):
            shots: list[list[tuple[float, float, float, float]]] = []

            last_y = doc_in.core_y.min
            for block in page_in.big_blocks[i]:
                r = (column.min, last_y, column.max, block["bbox"][1])
                if r[3] - r[1] > 0:
                    shots.append([r])
                else:
                    self.logger.warning(f"r.y1 <= r.y0, r = {r}")
                last_y = block["bbox"][3]
            shots.append([(column.min, last_y, column.max, doc_in.core_y.max)])

            column_shots.append(shots)

        elements_rect = []
        for block in page_in.raw_dict["blocks"]:
            elements_rect.append(block["bbox"])
        for draw in page_in.drawings:
            elements_rect.append(draw["rect"])

        # extend first rect in each column

        for shots in column_shots:
            if len(shots) == 0:
                continue
            first_shot = shots[0]
            if len(first_shot) != 1:
                raise Exception("len(first_shot) != 1")

            intersect_rects = []  # elements intersect with rect
            for r in elements_rect:
                if rectangle_relation(first_shot[0], r) == RectRelation.INTERSECT:
                    intersect_rects.append(r)

            if not intersect_rects:
                continue

            min_y0 = min([r[1] for r in intersect_rects])
            min_y0 = min(min_y0, first_shot[0][1])
            first_shot[0] = (
                first_shot[0][0],
                min_y0,
                first_shot[0][2],
                first_shot[0][3],
            )

        # delete empty rects
        BORDER_WIDTH = 4
        for shots in column_shots:
            for i in reversed(range(len(shots))):
                shot = shots[i]
                if len(shot) != 1:
                    raise Exception("len(shot) != 1")

                # delete height too small
                if shot[0][3] - shot[0][1] <= BORDER_WIDTH * 2:
                    del shots[i]
                    continue

                inner_rect = (
                    shot[0][0] + BORDER_WIDTH,
                    shot[0][1] + BORDER_WIDTH,
                    shot[0][2] - BORDER_WIDTH,
                    shot[0][3] - BORDER_WIDTH,
                )
                is_found = False
                for r in elements_rect:
                    if rectangle_relation(inner_rect, r) != RectRelation.NOT_INTERSECT:
                        is_found = True
                        break
                if not is_found:
                    del shots[i]

        # merge shot in different columns

        def is_near(shot1, shot2):
            rect1 = get_min_bounding_rect(shot1)
            rect2 = get_min_bounding_rect(shot2)
            for r in elements_rect:
                if (
                    rectangle_relation(rect1, r) == RectRelation.INTERSECT
                    and rectangle_relation(rect2, r) == RectRelation.INTERSECT
                ):
                    return True
            return False

        for i, shots in enumerate(column_shots):
            if i == len(column_shots) - 1:
                # The last column does not need to be merged
                break

            for j in range(len(shots)):
                cur_shot = shots[j]

                # TODO ZmICE1 - 2.png
                for other_c_index in range(i + 1, len(column_shots)):
                    next_c = column_shots[other_c_index]
                    is_find_near = False
                    for k in range(len(next_c)):
                        next_shot = next_c[k]
                        if is_near(cur_shot, next_shot):
                            is_find_near = True
                            shots[j].extend(next_shot)
                            del next_c[k]
                            break
                    if not is_find_near:
                        break

        return PageOutParams(column_shots), LocalPageOutParams()
