
def mrr_score(pred_item: list[str], gold_ranking: list[str]) -> float:
    """
    pred_item: 모델이 예측한 아이템 (예: "item_10")
    gold_ranking: 사람이 매긴 순위 리스트 (예: ["item_1", "item_2", "item_3"])
    """
    if pred_item not in gold_ranking:
        return 0.0
    rank = gold_ranking.index(pred_item) + 1
    return 1 / rank


def hit_at_k(pred_item: list[str], gold_ranking: list[str], k=3) -> float:
    """
    pred_item: 모델이 예측한 아이템 (예: "item_10")
    gold_ranking: 사람이 매긴 순위 리스트 (예: ["item_1", "item_2", "item_3"])
    """
    return 1.0 if pred_item in gold_ranking[:k] else 0.0