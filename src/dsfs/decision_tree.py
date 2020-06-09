from collections import Counter, defaultdict
import math
from typing import List, Any, Dict, TypeVar, Union, NamedTuple

T = TypeVar("T")


def entropy(class_probabilities: List[float]) -> float:
    return sum(-p * math.log(p, 2) for p in class_probabilities if p > 0)


def class_probabilities(labels: List[Any]) -> List[float]:
    total_count = len(labels)
    return [count / total_count for count in Counter(labels).values()]


def data_entropy(labels: List[Any]) -> float:
    return entropy(class_probabilities(labels))


def partition_entropy(subsets: List[List[Any]]) -> float:
    total_count = sum(len(subset) for subset in subsets)

    return sum(data_entropy(subset) * len(subset) / total_count for subset in subsets)


def partition_by(inputs: List[T], attribute: str) -> Dict[Any, List[T]]:
    partitions: Dict[Any, List[T]] = defaultdict(list)
    for inp in inputs:
        key = getattr(inp, attribute)
        partitions[key].append(inp)
    return partitions


def partition_entropy_by(inputs: List[Any], attribute: str, label_attribute: str) -> float:
    partitions = partition_by(inputs, attribute)

    labels = [
        [getattr(inp, label_attribute) for inp in partition] for partition in partitions.values()
    ]

    return partition_entropy(labels)


class Leaf(NamedTuple):
    value: Any


class Split(NamedTuple):
    attribute: str
    subtrees: dict
    default_value: Any = None


DecisionTree = Union[Leaf, Split]


def classify(tree: DecisionTree, input: Any) -> Any:
    if isinstance(tree, Leaf):
        return tree.value

    subtree_key = getattr(input, tree.attribute)

    if subtree_key not in tree.subtrees:
        return tree.default_value

    subtree = tree.subtrees[subtree_key]
    return classify(subtree, input)


def build_tree_id3(
    inputs: List[Any], split_attributes: List[str], target_attribute: str
) -> DecisionTree:
    label_counts = Counter(getattr(input, target_attribute) for input in inputs)
    most_common_label = label_counts.most_common(1)[0][0]

    if len(label_counts) == 1:
        return Leaf(most_common_label)

    if not split_attributes:
        return Leaf(most_common_label)

    def split_entropy(attribute: str) -> float:
        return partition_entropy_by(inputs, attribute, target_attribute)

    best_attribute = min(split_attributes, key=split_entropy)

    partitions = partition_by(inputs, best_attribute)
    new_attributes = [a for a in split_attributes if a != best_attribute]

    subtrees = {
        attribute_value: build_tree_id3(subset, new_attributes, target_attribute)
        for attribute_value, subset in partitions.items()
    }
    return Split(best_attribute, subtrees, default_value=most_common_label)
