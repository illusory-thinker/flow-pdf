from .common import Worker
from .common import DocInputParams, PageInputParams, DocOutputParams, PageOutputParams

from dataclasses import dataclass

from htutil import file


@dataclass
class DocInParams(DocInputParams):
    most_common_font: str
    most_common_size: int


@dataclass
class PageInParams(PageInputParams):
    raw_dict: dict


@dataclass
class DocOutParams(DocOutputParams):
    pass


@dataclass
class PageOutParams(PageOutputParams):
    pass


class DumpWorker(Worker):
    def __init__(self) -> None:
        super().__init__()

        self.disable_cache = True

    def run(  # type: ignore[override]
        self, doc_in: DocInParams, page_in: list[PageInParams]
    ) -> tuple[DocOutParams, list[PageOutParams]]:
        file.write_json(
            doc_in.dir_output / "meta.json", {"page_count": doc_in.page_count}
        )

        dir_raw_dict = doc_in.dir_output / "raw_dict"
        for page_index, p_i in enumerate(page_in):
            file.write_json(dir_raw_dict / f"{page_index}.json", p_i.raw_dict)

        file_meta = doc_in.dir_output / "meta.json"
        file.write_json(
            file_meta,
            {
                "most_common_font": doc_in.most_common_font,
                "most_common_size": doc_in.most_common_size,
            },
        )

        return (DocOutParams(), [])
