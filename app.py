import math
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Malgun Gothic'

st.set_page_config(page_title="총괄생산계획 웹앱", layout="wide")

# Level 전략 계산
def level_plan(monthly_demand, init_inventory, init_workers, prod_per_worker,
               max_overtime, regular_cost, overtime_cost, inventory_cost,
               shortage_cost, hire_cost, fire_cost):

    total_demand = sum(monthly_demand)
    avg_demand = total_demand / len(monthly_demand)

    workers = math.ceil(avg_demand / prod_per_worker)
    inventory = init_inventory
    rows = []

    hired = max(workers - init_workers, 0)
    fired = max(init_workers - workers, 0)

    for i in range(len(monthly_demand)):
        month = f"{i+1}월"
        demand = monthly_demand[i]

        begin_inventory = inventory
        regular_prod = workers * prod_per_worker

        production = regular_prod
        overtime_prod = 0

        end_value = begin_inventory + production - demand

        if end_value >= 0:
            ending_inventory = end_value
            shortage = 0
        else:
            ending_inventory = 0
            shortage = -end_value

        month_hire_cost = hire_cost * hired if i == 0 else 0
        month_fire_cost = fire_cost * fired if i == 0 else 0

        total_cost = (
            regular_prod * regular_cost
            + overtime_prod * overtime_cost
            + ending_inventory * inventory_cost
            + shortage * shortage_cost
            + month_hire_cost
            + month_fire_cost
        )

        rows.append({
            "월": month,
            "수요": demand,
            "기초재고": begin_inventory,
            "인원수": workers,
            "정규생산": regular_prod,
            "잔업생산": overtime_prod,
            "총생산량": production,
            "기말재고": ending_inventory,
            "부족량": shortage,
            "고용수": hired if i == 0 else 0,
            "해고수": fired if i == 0 else 0,
            "월총비용": total_cost
        })

        inventory = ending_inventory

    return pd.DataFrame(rows)


# Chase 전략 계산
def chase_plan(monthly_demand, init_inventory, init_workers, prod_per_worker,
               max_overtime, regular_cost, overtime_cost, inventory_cost,
               shortage_cost, hire_cost, fire_cost):

    inventory = init_inventory
    current_workers = init_workers
    rows = []

    for i in range(len(monthly_demand)):
        month = f"{i+1}월"
        demand = monthly_demand[i]
        begin_inventory = inventory

        need_production = max(demand - begin_inventory, 0)
        required_workers = math.ceil(need_production / prod_per_worker)

        hired = max(required_workers - current_workers, 0)
        fired = max(current_workers - required_workers, 0)

        current_workers = required_workers

        regular_prod = current_workers * prod_per_worker

        overtime_limit = int(regular_prod * max_overtime)
        remaining_need = max(need_production - regular_prod, 0)
        overtime_prod = min(remaining_need, overtime_limit)

        production = regular_prod + overtime_prod

        end_value = begin_inventory + production - demand

        if end_value >= 0:
            ending_inventory = end_value
            shortage = 0
        else:
            ending_inventory = 0
            shortage = -end_value

        total_cost = (
            regular_prod * regular_cost
            + overtime_prod * overtime_cost
            + ending_inventory * inventory_cost
            + shortage * shortage_cost
            + hired * hire_cost
            + fired * fire_cost
        )

        rows.append({
            "월": month,
            "수요": demand,
            "기초재고": begin_inventory,
            "인원수": current_workers,
            "정규생산": regular_prod,
            "잔업생산": overtime_prod,
            "총생산량": production,
            "기말재고": ending_inventory,
            "부족량": shortage,
            "고용수": hired,
            "해고수": fired,
            "월총비용": total_cost
        })

        inventory = ending_inventory

    return pd.DataFrame(rows)


# 선 그래프
def draw_line_chart(plan_df, title):
    fig, ax = plt.subplots(figsize=(9, 4))
    x_labels = [f"M{i+1}" for i in range(len(plan_df))]
    ax.plot(x_labels, plan_df["수요"], marker="o", label="Demand")
    ax.plot(x_labels, plan_df["총생산량"], marker="o", label="Production")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)


# 재고/부족 그래프
def draw_inventory_chart(plan_df, title):
    fig, ax = plt.subplots(figsize=(9, 4))
    x_labels = [f"M{i+1}" for i in range(len(plan_df))]
    ax.bar(x_labels, plan_df["기말재고"], label="Inventory")
    ax.bar(x_labels, plan_df["부족량"], label="Shortage")
    ax.set_title(title)
    ax.legend()
    st.pyplot(fig)


# 비용 비교
def draw_cost_chart(level_df, chase_df):
    compare_df = pd.DataFrame({
        "월": level_df["월"],
        "Level": level_df["월총비용"],
        "Chase": chase_df["월총비용"]
    })

    fig, ax = plt.subplots(figsize=(10, 4))
    x = range(len(compare_df))
    width = 0.35

    ax.bar([i - width/2 for i in x], compare_df["Level"], width=width, label="Level")
    ax.bar([i + width/2 for i in x], compare_df["Chase"], width=width, label="Chase")

    ax.set_xticks(list(x))
    ax.set_xticklabels([f"M{i+1}" for i in range(len(compare_df))])
    ax.set_title("Monthly Cost Comparison")
    ax.legend()
    st.pyplot(fig)


# 제목
st.title("총괄생산계획 계산 웹앱")

# 입력
st.sidebar.header("입력값")

default_demand = [135, 150, 142, 180, 210, 195, 220, 205, 190, 170, 160, 145]
monthly_demand = []

for i in range(12):
    value = st.sidebar.number_input(f"{i+1}월 수요", value=default_demand[i])
    monthly_demand.append(value)

init_inventory = st.sidebar.number_input("초기 재고", value=40)
init_workers = st.sidebar.number_input("초기 인원수", value=6)
prod_per_worker = st.sidebar.number_input("1인 생산량", value=30)
max_overtime = st.sidebar.number_input("잔업 비율", value=0.2)

regular_cost = st.sidebar.number_input("정규생산 단가", value=50000.0)
overtime_cost = st.sidebar.number_input("잔업 단가", value=70000.0)
inventory_cost = st.sidebar.number_input("재고 비용", value=5000.0)
shortage_cost = st.sidebar.number_input("부족 비용", value=12000.0)
hire_cost = st.sidebar.number_input("고용 비용", value=100000.0)
fire_cost = st.sidebar.number_input("해고 비용", value=120000.0)

# 계산
level_df = level_plan(monthly_demand, init_inventory, init_workers,
                      prod_per_worker, max_overtime, regular_cost,
                      overtime_cost, inventory_cost, shortage_cost,
                      hire_cost, fire_cost)

chase_df = chase_plan(monthly_demand, init_inventory, init_workers,
                      prod_per_worker, max_overtime, regular_cost,
                      overtime_cost, inventory_cost, shortage_cost,
                      hire_cost, fire_cost)

level_cost = level_df["월총비용"].sum()
chase_cost = chase_df["월총비용"].sum()

strategy = st.selectbox("전략 선택", ["Level 전략", "Chase 전략"])

if strategy == "Level 전략":
    df = level_df
    total_cost = level_cost
else:
    df = chase_df
    total_cost = chase_cost

# 결과 요약
st.subheader("결과 요약")

c1, c2, c3 = st.columns(3)
c1.metric("총비용", f"{total_cost:,.0f}")
c2.metric("총생산량", f"{df['총생산량'].sum():,}")
c3.metric("총부족량", f"{df['부족량'].sum():,}")

# 표
st.dataframe(df)

# 그래프
draw_line_chart(df, "Demand vs Production")
draw_inventory_chart(df, "Inventory and Shortage")
draw_cost_chart(level_df, chase_df)

# 간단 설명
if level_cost < chase_cost:
    best = "Level 전략"
else:
    best = "Chase 전략"

st.write(f"- 지금 입력 기준으로 보면 총비용은 {best}이 더 낮게 나왔습니다.")
st.write("- Level 전략은 인원을 유지해서 안정적이지만 재고가 늘어날 수 있습니다.")
st.write("- Chase 전략은 수요에 맞춰 생산해서 재고는 줄지만 인원 변화가 있습니다.")
st.write("- 수요나 비용을 바꾸면 결과가 바로 바뀌도록 만들었습니다.")
