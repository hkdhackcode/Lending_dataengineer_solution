 

create table clients (
	user_id integer not Null, 
	created_at timestamp without time zone not null,
	status varchar(20),
	batch integer,
	credit_limit bigint,
	interest_rate int,
	denied_reason varchar(200),
	denied_at timestamp without time zone,
	primary key (user_id)

)


create table loans(
	user_id int not null,
	loan_id bigint not null,
	created_at timestamp without time zone,
	due_at timestamp without time zone,
	paid_at timestamp without time zone,
	status varchar(20),
	loan_amount double precision,
	tax double precision,
	due_amount double precision,
	amount_paid double precision,
	primary key(loan_id), 
	constraint fk_client
		foreign key (user_id)
			references clients(user_id)
	
)


create table user_details(
	user_id integer primary key not null,
	user_name varchar(20),
	user_email varchar(20),
	user_adderss varchar(100),
	phone_number varchar(10)

);