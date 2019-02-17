import functools as ft
import itertools as it


@ft.lru_cache(maxsize=32)
def get_square_area_offsets(distance):
    offsets = list(it.product([i for i in range(-distance, distance + 1)], repeat=2))
    offsets.remove((0, 0))  # only offsets around current point required
    return set(offsets)


@ft.lru_cache(maxsize=32)
def get_square_offsets(distance):
    offsets = get_square_area_offsets(distance)
    for i in range(distance - 1, 0, -1):
        offsets = offsets.difference(get_square_area_offsets(i))
    return set(offsets)
