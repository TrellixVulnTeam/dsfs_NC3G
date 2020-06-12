from collections import deque, Counter
import random
from typing import NamedTuple, Dict, List, Tuple

import tqdm

from dsfs.linalg.matrix import Matrix, make_matrix, shape
from dsfs.linalg.vector import Vector, dot, magnitude, distance


class User(NamedTuple):
    id: int
    name: str


users = [
    User(0, "Hero"),
    User(1, "Dunn"),
    User(2, "Sue"),
    User(3, "Chi"),
    User(4, "Thor"),
    User(5, "Clive"),
    User(6, "Hicks"),
    User(7, "Devin"),
    User(8, "Kate"),
    User(9, "Klein"),
]

friend_pairs = [
    (0, 1),
    (0, 2),
    (1, 2),
    (1, 3),
    (2, 3),
    (3, 4),
    (4, 5),
    (5, 6),
    (5, 7),
    (6, 8),
    (7, 8),
    (8, 9),
]

endorsements = [
    (0, 1),
    (1, 0),
    (0, 2),
    (2, 0),
    (1, 2),
    (2, 1),
    (1, 3),
    (2, 3),
    (3, 4),
    (5, 4),
    (5, 6),
    (7, 5),
    (6, 8),
    (8, 7),
    (8, 9),
]


Friendships = Dict[int, List[int]]


def build_friendships(users: List[User]) -> Friendships:
    friendships: Friendships = {user.id: [] for user in users}
    for i, j in friend_pairs:
        friendships[i].append(j)
        friendships[j].append(i)

    return friendships


Path = List[int]


def shortest_path_from(from_user_id: int, friendships: Friendships) -> Dict[int, List[Path]]:
    shortest_paths_to: Dict[int, List[Path]] = {from_user_id: [[]]}
    frontier = deque((from_user_id, friend_id) for friend_id in friendships[from_user_id])

    while frontier:
        prev_user_id, user_id = frontier.popleft()

        paths_to_prev_user = shortest_paths_to[prev_user_id]
        new_paths_to_user = [path + [user_id] for path in paths_to_prev_user]

        old_paths_to_user = shortest_paths_to.get(user_id, [])

        if old_paths_to_user:
            min_path_length = len(old_paths_to_user[0])
        else:
            min_path_length = float("inf")

        new_paths_to_user = [
            path
            for path in new_paths_to_user
            if len(path) <= min_path_length and path not in old_paths_to_user
        ]
        shortest_paths_to[user_id] = old_paths_to_user + new_paths_to_user

        frontier.extend(
            (user_id, friend_id)
            for friend_id in friendships[user_id]
            if friend_id not in shortest_paths_to
        )

    return shortest_paths_to


def betweenness_centrality(users, friendships: Friendships):
    shortest_paths = {user.id: shortest_path_from(user.id, friendships) for user in users}

    betweenness = {user.id: 0.0 for user in users}
    for source in users:
        for target_id, paths in shortest_paths[source.id].items():
            if source.id < target_id:
                num_paths = len(paths)
                contrib = 1 / num_paths
                for path in paths:
                    for between_id in path:
                        if between_id not in [source.id, target_id]:
                            betweenness[between_id] += contrib

    return betweenness


def farness(user_id: int, shortest_paths) -> float:
    return sum(len(paths[0]) for paths in shortest_paths[user_id].values())


def closeness_centrality(users, friendships):
    shortest_paths = {user.id: shortest_path_from(user.id, friendships) for user in users}
    return {user.id: 1 / farness(user.id, shortest_paths) for user in users}


def matrix_times_matrix(m1: Matrix, m2: Matrix) -> Matrix:
    nr1, nc1 = shape(m1)
    nr2, nc2 = shape(m2)
    assert nc1 == nr2

    def entry_fn(i: int, j: int) -> float:
        return sum(m1[i][k] * m2[k[j]] for k in range(nc1))

    return make_matrix(nr1, nc2, entry_fn)


def matrix_times_vector(m: Matrix, v: Vector) -> Vector:
    nr, nc = shape(m)
    n = len(v)
    assert nc == n

    return [dot(row, v) for row in m]


def find_eigenvector(m: Matrix, tolerance: float = 0.00001) -> Tuple[Vector, float]:
    guess = [random.random() for _ in m]
    while True:
        result = matrix_times_vector(m, guess)
        norm = magnitude(result)
        next_guess = [x / norm for x in result]

        if distance(guess, next_guess) < tolerance:
            return next_guess, norm

        guess = next_guess


def make_adjacency_matrix(friend_pairs):
    def entry_fn(i: int, j: int):
        return 1 if (i, j) in friend_pairs or (j, i) in friend_pairs else 0

    n = len(users)
    return make_matrix(n, n, entry_fn)


def page_rank(
    users: List[User],
    endorsements: List[Tuple[int, int]],
    damping: float = 0.85,
    num_iters: int = 100,
) -> Dict[int, float]:
    outgoing_counts = Counter(target for source, target in endorsements)

    num_users = len(users)
    pr = {user.id: 1 / num_users for user in users}

    base_pr = (1 - damping) / num_users

    for iter in tqdm.trange(num_iters):
        next_pr = {user.id: base_pr for user in users}
        for source, target in endorsements:
            next_pr[target] += damping * pr[source] / outgoing_counts[source]
        pr = next_pr
    return pr
