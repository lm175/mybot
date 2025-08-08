from datetime import datetime

async def get_date(end_date: datetime):
    now = datetime.now()
    days = (end_date - now).days
    weeks = (days - 4) // 7 + 1
    return days, weeks


async def transform(maps, pieces):
    count = 0
    while True:
        count += maps
        pieces += maps
        maps = 0
        if pieces >= 10:
            maps = pieces // 10
            pieces %= 10
        else:
            break
    return count, pieces


async def caculator(current: list[int], days: int, weeks: int) -> list[int]:
    # 返回的列表储存计算结果，通用 属性 随机 凡品···随机
    result = [0] * 8

    # 计算初始碎片和图纸个数
    fanpin_pie = current[4] + days * 3
    random_pie = current[8] + days * 19
    fanpin = current[0] + random_pie // 10 + fanpin_pie // 10
    fanpin_pie %= 10

    zhenpin_pie = current[5] + days * 2
    zhenpin = current[1] + zhenpin_pie // 10
    zhenpin_pie %= 10

    juepin_pie = current[6] + days
    juepin = current[2] + juepin_pie // 10
    juepin_pie %= 10

    shenpin_pie = current[7] + weeks * 3
    shenpin = current[3] + shenpin_pie // 10


    # 将图纸转化成碎片
    fanpin_cnt, result[3] = await transform(fanpin, fanpin_pie)
    zhenpin_cnt, result[4] = await transform(zhenpin, zhenpin_pie)
    juepin_cnt, result[5] = await transform(juepin, juepin_pie)
    shenpin_cnt = shenpin
    result[6] = shenpin_pie % 10
    result[7] = random_pie % 10


    # 计算残卷数量
    result[0] = days * 29 + weeks * 40 + fanpin_cnt * 5 + zhenpin_cnt * 10 + juepin_cnt * 20 + shenpin_cnt * 40
    result[1] = days * 22 + weeks * 30 + juepin_cnt * 16 + shenpin_cnt * 30
    result[2] = fanpin_cnt * 4 + zhenpin_cnt * 8

    return result


async def get_total_element_fragment(current: list[int]) -> tuple[str, int, int]:
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
    total = 0
    for k, v in element_map.items():
        if k != max_element:
            total += v // 2
    return max_element, max_value, total