def get_total_element_fragment(current: list[int]) -> tuple[str, int]:
    element_map = {
        "风": current[9],
        "雷": current[10],
        "水": current[11],
        "火": current[12]
    }
    max_element = ""
    max_value = 0
    for k, v in element_map.items():
        if v > max_value:
            max_value = v
            max_element = k
    total = max_value
    for k, v in element_map.items():
        if k != max_element:
            total += v // 2
    return max_element, total

print(get_total_element_fragment([0,0,0,0,0,0,0,0,0,22,32,32,86,500]))