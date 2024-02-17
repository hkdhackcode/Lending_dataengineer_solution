-- Question : Identify the best month in terms of loan issuance. What was the quantity and amount lent in each month?
with cte as (select 
extract(year from created_at) as years,
extract(month from created_at) as months,
count(user_id) as cnt,
sum(loan_amount) as total_loan_amount,
sum(due_amount - (loan_amount + tax)) as expected_earning
from loans 
group by years, months)
select * , 100*expected_earning/total_loan_amount as per from cte;

-- best month is  dec 2023, most number of loan is issued and largest quantity




-- Question: Determine which batch had the best overall adherence?

with cte as (
select batch, count(l.loan_id) as loan_issued, 
count(case when l.status = 'default' then 1 else null end) as default_cnt, 
count(case when l.status = 'paid' then 1 else null end) as paid_cnt, 
count(case when l.status = 'ongoing' then 1 else null end) as ongoing_cnt, 
sum(loan_amount) as issued_amount,
sum(case when l.status = 'default' then loan_amount else 0 end)as default_amount, 
sum(case when l.status = 'paid' then loan_amount else 0 end)as paid_amount, 
sum(case when l.status = 'ongoing' then loan_amount else 0 end)as ongoing_amount
from clients c join loans l
on c.user_id = l.user_id
group by batch
)
select * , 
default_amount*100.0/issued_amount as default_rate_amount,
paid_amount*100.0/issued_amount as paid_rate_amount,
ongoing_amount*100.0/issued_amount as ongoing_rate_amount,
default_cnt*100.0/loan_issued as default_rate,
paid_cnt*100.0/loan_issued as paid_rate,
ongoing_cnt*100.0/loan_issued as ongoing_rate


from cte;

 -- batch 3 has best overall adhereance with lowest default rate



-- Question : Do different interest rates lead to different loan outcomes in terms of default rate?



select interest_rate, count(l.loan_id) as loan_issued, 
count(case when l.status = 'default' then 1 else null end) as default_cnt,
count(case when l.status = 'default' then 1 else null end)*100.0/count(l.loan_id) as default_rate
from clients c join loans l
on c.user_id = l.user_id
group by interest_rate;

-- yes low interest result in low default rate, but diffrence is very small.




-- Question : Rank the best 10 and 10 worst clients. Explain your methodology for constructing this ranking


-- Top 10 best clients

with cte as (
select c.user_id, count(loan_id) as cnt, sum(loan_amount) as total_due_amount, 
	sum(case when l.status = 'paid' then amount_paid else 0 end) as total_paid_amount,
	sum(case when l.status = 'paid' then amount_paid else 0 end)/sum(loan_amount) as repayment_ratio,
	extract(day from avg(paid_at - l.created_at)) as diff
from clients c join loans l
on c.user_id = l.user_id
where c.status = 'approved'
group by c.user_id
),
normalized_data as (
select *, 
((total_paid_amount - min(total_paid_amount) over()) / (max(total_paid_amount) over() - min(total_paid_amount) over()))  as paid_amount_normalize,
((repayment_ratio - min(repayment_ratio) over()) / (max(repayment_ratio) over() - min(repayment_ratio) over()))  as repayment_ratio_normalize ,
((max(diff) over() - diff) / (max(diff) over() - min(diff) over()))  as diff_normalize 

from cte
where diff is not null
)
select user_id,round(cast(total_paid_amount as numeric), 2), round(cast(repayment_ratio as numeric), 2), diff as avg_return_time,
round(cast(((0.5*paid_amount_normalize) + (0.3*diff_normalize) + (0.2*repayment_ratio_normalize)) as numeric), 2) as score
from normalized_data
order by score  desc;




 -- Top 10 worst clients
 
 
select c.user_id , sum(due_amount - amount_paid) as unpaid_amount
from clients c join loans l
on c.user_id = l.user_id
where l.status = 'default'
group by c.user_id
order by unpaid_amount desc;



-- Question : What is the default rate by month and by batch?

-- Default rate by batch
select c.batch, count(l.loan_id) as loan_issued, 
count(case when l.status = 'default' then 1 else null end) as default_cnt,
count(case when l.status = 'default' then 1 else null end)*100.0/count(l.loan_id) as default_rate
from clients c join loans l
on c.user_id = l.user_id
group by c.batch;



-- Default rate by month

select extract(year from l.created_at) as years,
extract(month from l.created_at) as months, count(l.loan_id) as loan_issued, 
count(case when l.status = 'default' then 1 else null end) as default_cnt,
count(case when l.status = 'default' then 1 else null end)*100.0/count(l.loan_id) as default_rate
from clients c join loans l
on c.user_id = l.user_id
group by years, months;


-- Assess the profitability of this operation. Provide an analysis of the operation's timeline.


-- monthly analysis

with cte as (select 
extract(year from created_at) as years,
extract(month from created_at) as months,
count(user_id) as cnt,
sum(loan_amount) as total_loan_amount,
sum(amount_paid) as total_amount_paid,
sum(amount_paid - (loan_amount + tax)) as total_earning,
sum(case when status = 'default' then due_amount else 0 end) as default_amount
from loans 
group by years, months),
with_lags as (select *,lag(total_loan_amount) over(order by years, months) as previous_month, 
			  (100*total_earning/total_loan_amount)as earning_rate
			  from cte)

select years, months, cnt as Numeber_of_loan_issued, round(CAST(total_loan_amount as numeric), 2) as total_loan_amoun,
round(CAST(default_amount as numeric), 2) as default_amount, 
round(CAST(total_amount_paid as numeric), 2) as total_amound_paid,
round(CAST(total_earning as numeric), 2) as total_earning,
round(CAST(earning_rate as numeric), 2) as earning_rate,  
round(CAST(((total_loan_amount -  previous_month)*100/previous_month) as numeric), 2) as growth_percentage
from with_lags;


-- yearly analysis

with cte as (
select extract(year from l.created_at) as years, count(l.loan_id) as loan_issued, 
count(case when l.status = 'default' then 1 else null end) as default_cnt, 
count(case when l.status = 'paid' then 1 else null end) as paid_cnt, 
count(case when l.status = 'ongoing' then 1 else null end) as ongoing_cnt, 
sum(loan_amount) as issued_amount,
sum(case when l.status = 'default' then loan_amount else 0 end)as default_amount, 
sum(case when l.status = 'paid' then loan_amount else 0 end)as paid_amount, 
sum(case when l.status = 'ongoing' then loan_amount else 0 end)as ongoing_amount
from clients c join loans l
on c.user_id = l.user_id
group by extract(year from l.created_at)
)
select * , 

round((default_cnt*100.0/loan_issued), 2) as default_rate,
round((paid_cnt*100.0/loan_issued), 2) as paid_rate,
round((ongoing_cnt*100.0/loan_issued), 2) as ongoing_rate

from cte;

