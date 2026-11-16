"""Unit tests for cache key generation and parameter normalization."""

from app.cache.keys import (
    dashboard_stats_generation_key,
    dashboard_stats_key,
    get_prefix,
    product_detail_key,
    product_list_generation_key,
    product_list_key,
)


def test_prefix_default():
    assert get_prefix() == "v1"


def test_product_detail_key():
    assert product_detail_key(101) == "v1:product:101"
    assert product_detail_key(42) == "v1:product:42"


def test_generation_keys():
    assert product_list_generation_key() == "v1:cachegen:products:list"
    assert dashboard_stats_generation_key() == "v1:cachegen:dashboard:stats"


def test_product_list_key_normalization():
    # Category with whitespace and mixed case
    key1 = product_list_key(
        generation=1,
        category="  Electronics  ",
        page=1,
        limit=20,
        sort_by="PRICE",
        sort_order="ASC",
    )
    assert key1 == "v1:products:list:g1:cat:electronics:page:1:limit:20:sort:price:asc"

    # Category None should normalize to 'all'
    key2 = product_list_key(
        generation=2,
        category=None,
        page=2,
        limit=50,
        sort_by="name",
        sort_order="desc",
    )
    assert key2 == "v1:products:list:g2:cat:all:page:2:limit:50:sort:name:desc"

    # Whitespace-only category should normalize to 'all'
    key3 = product_list_key(
        generation=1,
        category="   ",
        page=1,
        limit=10,
        sort_by="id",
        sort_order="asc",
    )
    assert key3 == "v1:products:list:g1:cat:all:page:1:limit:10:sort:id:asc"


def test_dashboard_stats_key():
    assert dashboard_stats_key(1) == "v1:dashboard:stats:g1"
    assert dashboard_stats_key(5) == "v1:dashboard:stats:g5"
