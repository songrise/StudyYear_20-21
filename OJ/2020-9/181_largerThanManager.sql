-- # Write your MySQL query statement below

select e1.Name as Employee
from Employee as e1, Employee as e2
where e1.ManagerId = e2.Id and e1.Salary > e2.Salary


