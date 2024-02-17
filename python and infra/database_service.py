import psycopg2
from psycopg2 import sql
import json
from datetime import datetime

class Database:

    def __init__(self, config) -> None:
        self.user = config["user"]
        self.host = config["host"]
        self.database = config["database"]
        self._password = config["password"]
        self.port = config["port"]
        self.connection = None

    def get_connection(self):
        try:
            self.connection = psycopg2.connect(database = self.database, 
                                    user = self.user, 
                                    host= self.host,
                                    password = self._password,
                                    port = self.port)
            return self.connection
        except psycopg2.Error as e:
            print(f"Error connecting to the database: {e}")
            return None
        
    def close_connection(self):
        if self.connection:
            connection.close()

    
    def add_new_user(self,
                    user_id : int, 
                    status: str, 
                    batch: int, 
                    credit_limit: float, 
                    interest_rate: float,
                    denied_reason: str = None) -> None:

        if self.connection is None:
            self.connection = self.get_connection()
        try:
            with self.connection.cursor() as cursor:
                insert_sql = sql.SQL('''
                    INSERT INTO clients (user_id, created_at, status, batch, credit_limit, interest_rate,denied_reason, denied_at )
                    VALUES (%(user_id)s, %(created_at)s, %(status)s,
                            %(batch)s, %(credit_limit)s, %(interest_rate)s,
                            %(denied_reason)s, %(denied_at)s);
                ''')

                created_time = datetime.now()
                if status == "denied":
                    denied_time = datetime.now()
                else:
                    denied_reason = None
                    denied_time = None
                
                values = {
                        "user_id":user_id, 
                        "created_at":created_time,
                        "status":status,
                        "batch": batch,
                        "credit_limit": credit_limit, 
                        "interest_rate":interest_rate,
                        "denied_reason":denied_reason, 
                        "denied_at":denied_time 
                        }
                cursor.execute(insert_sql, values)
            self.connection.commit()
            print(f"User with ID {user_id} added successfully.")
        except psycopg2.Error as e:
            self.connection.rollback()
            print(f"Error adding user: {e}")
        
    
    def update_user_details(self, 
                            user_id : int, 
                            status: str, 
                            credit_limit: float, 
                            interest_rate: float,
                            denied_reason: str = None) -> None:
        if self.connection is None:
            self.conection = self.get_connection()
        try:
            with self.connection.cursor() as cursor:
                update_sql = sql.SQL('''
                    UPDATE clients
                    SET status =  %(status)s,
                        credit_limit = %(credit_limit)s, 
                        interest_rate = %(interest_rate)s,
                        denied_reason = %(denied_reason)s,
                        denied_at = %(denied_at)s
                    WHERE user_id = %(user_id)s;
                ''')

                if status == "denied":
                    denied_time = datetime.now()
                else:
                    denied_reason = None
                    denied_time = None
                
                values = {
                        "user_id":user_id, 
                        "status":status,
                        "credit_limit": credit_limit, 
                        "interest_rate":interest_rate,
                        "denied_reason":denied_reason, 
                        "denied_at":denied_time
                        }
                
                cursor.execute(update_sql, values)
            self.connection.commit()
            print(f"Details for user with ID {user_id} updated successfully.")

        except psycopg2.Error as e:
            self.connection.rollback()
            print(f"Error updating status: {e}")
    
    def check_due_payment(self):
        if self.connection is None:
            self.connection = self.get_connection()
        try:
            with self.connection.cursor() as cursor:
                check_sql = sql.SQL('''
                    select u.user_id, user_name, user_email, due_amount, due_at, extract(day from due_at - now()) as due_in
                    from user_details u
                    join loans l
                    on u.user_id = l.user_id
                    where l.status = 'ongoing' and due_at > now();
                ''')
                cursor.execute(check_sql)
                results = cursor.fetchall()
            return results
        except psycopg2.Error as e:
            print(f"Error updating status: {e}")

    def get_last_week_status(self):
        if self.connection is None:
            self.connection = self.get_connection()
        try:
            with self.connection.cursor() as cursor:
                status_sql = sql.SQL('''
                    with new_loan as (
                    select count(loan_id) as loan_issued, sum(loan_amount) as total_issued_amount
                    from loans
                    where created_at > now() - interval '70 days'),
                    repayment_status as 
                    (select count(loan_id) as loan_paid, sum(amount_paid) as total_paid_amount
                    from loans
                    where paid_at > now() - interval '70 days')
                    select * from new_loan, repayment_status;
                ''')
                cursor.execute(status_sql)
                results = cursor.fetchall()
            return results
        except psycopg2.Error as e:
            print(f"Error updating status: {e}")
    
    def get_overall_summary(self):
        if self.connection is None:
            self.connection = self.get_connection()
        try:
            with self.connection.cursor() as cursor:
                status_sql = sql.SQL('''
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
                ''')
                cursor.execute(status_sql)
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
            return results, columns
        except psycopg2.Error as e:
            print(f"Error updating status: {e}")

    def get_overall_summary_monthly(self):
        if self.connection is None:
            self.connection = self.get_connection()
        try:
            with self.connection.cursor() as cursor:
                status_sql = sql.SQL('''
                                with cte as (
                                    select 
                                    extract(year from created_at) as years,
                                    extract(month from created_at) as months,
                                    count(user_id) as cnt,
                                    sum(loan_amount) as total_loan_amount,
                                    sum(amount_paid) as total_amount_paid,
                                    sum(amount_paid - (loan_amount + tax)) as total_earning,
                                    sum(case when status = 'default' then due_amount else 0 end) as default_amount
                                    from loans 
                                    group by years, months
                                ),
                                with_lags as (select *,lag(total_loan_amount) over(order by years, months) as previous_month, 
                                            (100*total_earning/total_loan_amount)as earning_rate
                                            from cte)

                                select years, months, 
                                cnt as Numeber_of_loan_issued, 
                                round(CAST(total_loan_amount as numeric), 2) as total_loan_amoun,
                                round(CAST(default_amount as numeric), 2) as default_amount, 
                                round(CAST(total_amount_paid as numeric), 2) as total_amound_paid,
                                round(CAST(total_earning as numeric), 2) as total_earning,
                                round(CAST(earning_rate as numeric), 2) as earning_rate,  
                                round(CAST(((total_loan_amount -  previous_month)*100/previous_month) as numeric), 2) as growth_percentage
                                from with_lags;
                            ''')
                cursor.execute(status_sql)
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
            return results, columns

        except psycopg2.Error as e:
            print(f"Error updating status: {e}")

def calculate_frequency(days_until_due):
    if days_until_due >= 60:
        return 14  # One reminder per two week
    elif days_until_due >= 14:
        return 7  # one reminders per week
    elif days_until_due >=7:
        return 3  # two reminder per week
    else: 
        return 1 # daily remineder
    




if __name__ == "__main__":
    data = json.load(open('config.json'))
    print(data)
    config = data["db"]

    db = Database(config)
    conn = db.get_connection()
    #print(conn)
    #db.update_user_details(1244215, "denied", 10000, 30,"crime")
    #db.update_user_details(1, "Anu")

    output = db.get_overall_summary_monthly()
    cur = db.connection.cursor()
    
    #insert_sql = '''
    #    INSERT INTO sample_table (person_id, person_name)
    #    VALUES (%s, %s)
    #    ON CONFLICT (person_id) DO UPDATE SET
    #    (person_name) = ROW(EXCLUDED.person_name);
    #'''

    #cur.execute(insert_sql, (1, "Ankit"))
    cur.execute('Select * from clients where user_id = 1244215;')
    rows = [des[0] for des in cur.description]
    #rows = cur.fetchall()
    #db.connection.commit()
    db.connection.close()
    for row in rows:
        print(row)

