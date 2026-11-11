from cloud.domain.violation.priority import MIN_TENURE_SEC, CameraLoad, GridRanker


def load(cam: int, people: int = 0, violations: int = 0) -> CameraLoad:
    return CameraLoad(camera_id=cam, person_count=people, recent_violations=violations)


def test_camera_with_violations_ranks_first():
    ranker = GridRanker(size=3)
    order = ranker.rank([load(1), load(2, violations=2), load(3, people=3)], now=0)
    assert order[0] == 2


def test_only_size_cameras_are_shown():
    ranker = GridRanker(size=2)
    order = ranker.rank([load(i, people=i) for i in range(1, 6)], now=0)
    assert len(order) == 2
    assert order == [5, 4]


def test_no_swap_before_tenure_is_over():
    ranker = GridRanker(size=1)
    ranker.rank([load(1)], now=0)
    order = ranker.rank([load(1), load(2, violations=5)], now=MIN_TENURE_SEC - 1)
    assert order == [1]


def test_swap_after_tenure_when_newcomer_clearly_wins():
    ranker = GridRanker(size=1)
    ranker.rank([load(1)], now=0)
    order = ranker.rank([load(1), load(2, violations=5)], now=MIN_TENURE_SEC + 1)
    assert order == [2]


def test_small_difference_does_not_swap():
    ranker = GridRanker(size=1)
    ranker.rank([load(1, people=4)], now=0)
    order = ranker.rank([load(1, people=4), load(2, people=5)], now=MIN_TENURE_SEC + 1)
    assert order == [1]
