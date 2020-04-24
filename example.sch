project lasts 2020/4/1 to 2020/5/15
saturday are closed
sunday are closed
2020/5/1 is closed
today is 2020/4/20

tasks are colored #CCFF00/#00FF00/#000000/#FF00FF/#000000
milestones are colored blue/black/red/blue/yellow
paths are colored red

-- Milestone --
!milestone1: "Review"
  >! task2's end
  .! 2020/4/15

-- Task --
TK1
  >> 2020/4/10
  >= 10 days

TK2
  >> TK1's end
  >= 10 days

task1: "Task 1"
  >> project's start
  >= 10 days
  .> 2020/4/4
  .< 2020/4/10
  @alice

task2: 'Task 2'
  >> task1's end
  >= 5 days
  .> 2020/4/10
  .= 5 days
  @bob

task3: "Task 3"
  >> task2's end
  >< project's end
  .> 2020/4/15
  .- 20%
  @bob
