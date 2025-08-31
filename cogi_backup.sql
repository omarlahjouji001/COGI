--
-- PostgreSQL database dump
--

-- Dumped from database version 14.18 (Homebrew)
-- Dumped by pg_dump version 14.18 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: conversations; Type: TABLE; Schema: public; Owner: mac
--

CREATE TABLE public.conversations (
    id integer NOT NULL,
    user_email character varying(255),
    message text NOT NULL,
    sender character varying(20),
    "timestamp" timestamp with time zone DEFAULT now(),
    session_id uuid DEFAULT gen_random_uuid(),
    title text,
    CONSTRAINT conversations_sender_check CHECK (((sender)::text = ANY (ARRAY[('user'::character varying)::text, ('bot'::character varying)::text])))
);


ALTER TABLE public.conversations OWNER TO mac;

--
-- Name: conversations_id_seq; Type: SEQUENCE; Schema: public; Owner: mac
--

CREATE SEQUENCE public.conversations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.conversations_id_seq OWNER TO mac;

--
-- Name: conversations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mac
--

ALTER SEQUENCE public.conversations_id_seq OWNED BY public.conversations.id;


--
-- Name: feedback; Type: TABLE; Schema: public; Owner: mac
--

CREATE TABLE public.feedback (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    message text NOT NULL,
    submitted_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.feedback OWNER TO mac;

--
-- Name: feedback_id_seq; Type: SEQUENCE; Schema: public; Owner: mac
--

CREATE SEQUENCE public.feedback_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.feedback_id_seq OWNER TO mac;

--
-- Name: feedback_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mac
--

ALTER SEQUENCE public.feedback_id_seq OWNED BY public.feedback.id;


--
-- Name: subscriber; Type: TABLE; Schema: public; Owner: mac
--

CREATE TABLE public.subscriber (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    subscribed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.subscriber OWNER TO mac;

--
-- Name: subscriber_id_seq; Type: SEQUENCE; Schema: public; Owner: mac
--

CREATE SEQUENCE public.subscriber_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.subscriber_id_seq OWNER TO mac;

--
-- Name: subscriber_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mac
--

ALTER SEQUENCE public.subscriber_id_seq OWNED BY public.subscriber.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: mac
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    password text NOT NULL,
    first_name character varying(100),
    last_name character varying(100),
    gender character varying(10),
    dob date,
    confirmed boolean DEFAULT false,
    attempts integer DEFAULT 0
);


ALTER TABLE public.users OWNER TO mac;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: mac
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO mac;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mac
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: conversations id; Type: DEFAULT; Schema: public; Owner: mac
--

ALTER TABLE ONLY public.conversations ALTER COLUMN id SET DEFAULT nextval('public.conversations_id_seq'::regclass);


--
-- Name: feedback id; Type: DEFAULT; Schema: public; Owner: mac
--

ALTER TABLE ONLY public.feedback ALTER COLUMN id SET DEFAULT nextval('public.feedback_id_seq'::regclass);


--
-- Name: subscriber id; Type: DEFAULT; Schema: public; Owner: mac
--

ALTER TABLE ONLY public.subscriber ALTER COLUMN id SET DEFAULT nextval('public.subscriber_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: mac
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: conversations; Type: TABLE DATA; Schema: public; Owner: mac
--

COPY public.conversations (id, user_email, message, sender, "timestamp", session_id, title) FROM stdin;
\.


--
-- Data for Name: feedback; Type: TABLE DATA; Schema: public; Owner: mac
--

COPY public.feedback (id, name, message, submitted_at) FROM stdin;
1	Imane rhafour	Cogi helped me get through hard time 	2025-05-21 00:25:16.938824
\.


--
-- Data for Name: subscriber; Type: TABLE DATA; Schema: public; Owner: mac
--

COPY public.subscriber (id, email, subscribed_at) FROM stdin;
1	i.rhafour01@gmail.com	2025-05-21 00:30:06.159571
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: mac
--

COPY public.users (id, email, password, first_name, last_name, gender, dob, confirmed, attempts) FROM stdin;
1	i.rhafour01@gmail.com	pbkdf2:sha256:1000000$efjo8fNS5P3ozs0K$6a062c4620c93d94eddff6e124b49dd1fdf99ba1eda656a4fde36d3c9bd93cf5	Imane	RHAFOUR	female	2001-10-02	t	0
\.


--
-- Name: conversations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mac
--

SELECT pg_catalog.setval('public.conversations_id_seq', 26, true);


--
-- Name: feedback_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mac
--

SELECT pg_catalog.setval('public.feedback_id_seq', 1, true);


--
-- Name: subscriber_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mac
--

SELECT pg_catalog.setval('public.subscriber_id_seq', 1, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mac
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: conversations conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: mac
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_pkey PRIMARY KEY (id);


--
-- Name: feedback feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: mac
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_pkey PRIMARY KEY (id);


--
-- Name: subscriber subscriber_email_key; Type: CONSTRAINT; Schema: public; Owner: mac
--

ALTER TABLE ONLY public.subscriber
    ADD CONSTRAINT subscriber_email_key UNIQUE (email);


--
-- Name: subscriber subscriber_pkey; Type: CONSTRAINT; Schema: public; Owner: mac
--

ALTER TABLE ONLY public.subscriber
    ADD CONSTRAINT subscriber_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: mac
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: mac
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: conversations conversations_user_email_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mac
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_user_email_fkey FOREIGN KEY (user_email) REFERENCES public.users(email);


--
-- PostgreSQL database dump complete
--

