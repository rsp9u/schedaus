example_yaml = """
project:
  start: 2020/4/1
  end: 2020/5/15
  closed:
    - sat
    - sun
    - 2020/5/1
  today: 2020/4/20
task:
  - name: TK1
    plan:
      start: 2020/4/10
      period: 11 days
  - name: TK2
    plan:
      start: TK1's end
      period: 10 days
  - name: task1
    text: "Task 1"
    plan:
      start: project's start
      period: 4 days
    actual:
      start: 2020/4/4
      end: 2020/4/9
    assignee: alice
  - name: task2
    text: "タスク2"
    plan:
      start: task1's end
      end: milestone1's start
    actual:
      start: 2020/4/10
      period: 5 days
    assignee: bob
  - name: task3
    text: "Task 3"
    plan:
      start: task2's end
      end: project's end
    actual:
      start: 2020/4/17
      progress: 20%
    assignee: bob
  - name: task4
    text: "Task 4"
    plan:
      start: task2's end
      period: 6 days
  - name: task5
    text: "Task 5"
    plan:
      start: 2020/4/9
      period: 10 days
    actual:
      start: 2020/4/16
      progress: 30%
milestone:
  - name: milestone1
    text: "Review"
    plan: 2020/4/10
group:
  - text: Milestone
    member: [milestone1]
  - text: Task
    member: [TK1, TK2]
"""
