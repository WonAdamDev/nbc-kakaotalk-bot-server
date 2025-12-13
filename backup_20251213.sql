--
-- PostgreSQL database dump
--

\restrict fjHMNtqmKzuysmyS6F46H9W1z0bvPcbuTtL49zfODVpfPh8WgIyX9mUQzciHszI

-- Dumped from database version 17.7 (Debian 17.7-3.pgdg13+1)
-- Dumped by pg_dump version 18.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
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
-- Name: games; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.games (
    game_id character varying(8) NOT NULL,
    room character varying(100) NOT NULL,
    creator character varying(50),
    date date NOT NULL,
    created_at timestamp without time zone,
    started_at timestamp without time zone,
    ended_at timestamp without time zone,
    status character varying(20),
    current_quarter integer,
    final_score_blue integer,
    final_score_white integer,
    winner character varying(10),
    team_home character varying(50),
    team_away character varying(50),
    room_id character varying(8) NOT NULL
);


ALTER TABLE public.games OWNER TO postgres;

--
-- Name: lineups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.lineups (
    id integer NOT NULL,
    game_id character varying(8) NOT NULL,
    team character varying(10) NOT NULL,
    member character varying(50) NOT NULL,
    number integer NOT NULL,
    arrived boolean,
    arrived_at timestamp without time zone,
    playing_status character varying(10) DEFAULT 'playing'::character varying
);


ALTER TABLE public.lineups OWNER TO postgres;

--
-- Name: lineups_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.lineups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.lineups_id_seq OWNER TO postgres;

--
-- Name: lineups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.lineups_id_seq OWNED BY public.lineups.id;


--
-- Name: quarters; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.quarters (
    id integer NOT NULL,
    game_id character varying(8) NOT NULL,
    quarter_number integer NOT NULL,
    status character varying(20),
    playing_blue json,
    playing_white json,
    bench_blue json,
    bench_white json,
    score_blue integer,
    score_white integer,
    started_at timestamp without time zone,
    ended_at timestamp without time zone,
    lineup_snapshot json
);


ALTER TABLE public.quarters OWNER TO postgres;

--
-- Name: quarters_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.quarters_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.quarters_id_seq OWNER TO postgres;

--
-- Name: quarters_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.quarters_id_seq OWNED BY public.quarters.id;


--
-- Name: room_members; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.room_members (
    id integer NOT NULL,
    room character varying(100) NOT NULL,
    name character varying(50) NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.room_members OWNER TO postgres;

--
-- Name: room_members_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.room_members_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.room_members_id_seq OWNER TO postgres;

--
-- Name: room_members_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.room_members_id_seq OWNED BY public.room_members.id;


--
-- Name: rooms; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rooms (
    room_id character varying(8) NOT NULL,
    name character varying(100) NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.rooms OWNER TO postgres;

--
-- Name: lineups id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lineups ALTER COLUMN id SET DEFAULT nextval('public.lineups_id_seq'::regclass);


--
-- Name: quarters id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quarters ALTER COLUMN id SET DEFAULT nextval('public.quarters_id_seq'::regclass);


--
-- Name: room_members id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_members ALTER COLUMN id SET DEFAULT nextval('public.room_members_id_seq'::regclass);


--
-- Data for Name: games; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.games (game_id, room, creator, date, created_at, started_at, ended_at, status, current_quarter, final_score_blue, final_score_white, winner, team_home, team_away, room_id) FROM stdin;
8273D3DB	원동현	원동현	2025-12-12	2025-12-12 05:12:23.804849	2025-12-12 05:27:00.98356	\N	진행중	4	\N	\N	\N	블루	화이트	3A92DCDD
B6189566	원동현	원동현	2025-12-09	2025-12-09 12:49:29.727963	2025-12-10 13:17:50.682355	2025-12-12 03:00:05.324927	종료	1	0	0	무승부	\N	\N	3A92DCDD
75A46682	원동현	원동현	2025-12-12	2025-12-12 00:26:33.172064	2025-12-12 02:38:12.121314	\N	진행중	0	\N	\N	\N	\N	\N	3A92DCDD
B4EC16C0	원동현	원동현	2025-12-10	2025-12-10 13:48:29.658406	2025-12-10 13:59:30.389416	2025-12-10 14:31:09.307689	종료	4	52	60	화이트	\N	\N	3A92DCDD
6DE3713E	원동현	원동현	2025-12-09	2025-12-09 11:55:17.905145	2025-12-09 12:01:11.780728	2025-12-10 13:12:35.071928	종료	4	7	7	무승부	\N	\N	3A92DCDD
3338914D	원동현	원동현	2025-12-07	2025-12-07 09:28:19.961944	2025-12-07 09:30:37.743379	2025-12-07 09:36:44.670462	종료	4	50	60	화이트	\N	\N	3A92DCDD
F606932F	원동현	원동현	2025-12-07	2025-12-07 06:33:47.126777	2025-12-07 09:15:18.032459	2025-12-07 09:27:57.122718	종료	3	0	0	무승부	\N	\N	3A92DCDD
E582E789	DEBUG ROOM	DEBUG SENDER	2025-12-12	2025-12-12 04:55:29.090358	\N	\N	준비중	0	\N	\N	\N	\N	\N	5D8CB2B6
\.


--
-- Data for Name: lineups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.lineups (id, game_id, team, member, number, arrived, arrived_at, playing_status) FROM stdin;
1	F606932F	화이트	원동현	1	t	2025-12-07 09:15:40.182326	playing
2	F606932F	화이트	강현정	2	t	2025-12-07 09:15:47.575995	playing
3	F606932F	블루	감두희	1	t	2025-12-07 09:15:52.106664	playing
4	F606932F	블루	임수암	2	t	2025-12-07 09:16:08.918036	playing
5	F606932F	블루	이정기	3	t	2025-12-07 09:16:15.770709	playing
6	F606932F	화이트	박종희	3	t	2025-12-07 09:17:47.011461	playing
7	F606932F	화이트	배재혁	4	t	2025-12-07 09:18:05.302431	playing
8	F606932F	화이트	최명수	5	t	2025-12-07 09:18:14.465044	playing
9	F606932F	화이트	오현우	6	t	2025-12-07 09:18:20.55386	playing
10	F606932F	화이트	김희곤	7	t	2025-12-07 09:18:28.090806	playing
11	F606932F	블루	이상준	4	t	2025-12-07 09:18:32.604023	playing
12	F606932F	블루	남승우	5	t	2025-12-07 09:18:37.452267	playing
13	F606932F	블루	강종찬	6	t	2025-12-07 09:18:41.800834	playing
14	F606932F	블루	김동우	7	t	2025-12-07 09:18:47.155334	playing
15	F606932F	블루	장유진	8	t	2025-12-07 09:18:51.570191	playing
16	F606932F	화이트	김철희	8	t	2025-12-07 09:26:24.372505	playing
17	3338914D	블루	a	1	t	2025-12-07 09:28:34.27846	playing
18	3338914D	블루	b	2	t	2025-12-07 09:28:36.765947	playing
19	3338914D	블루	c	3	t	2025-12-07 09:28:39.269211	playing
20	3338914D	블루	d	4	t	2025-12-07 09:28:42.291634	playing
21	3338914D	블루	e	5	t	2025-12-07 09:28:44.718732	playing
22	3338914D	블루	f	6	t	2025-12-07 09:28:47.094048	playing
23	3338914D	블루	g	7	t	2025-12-07 09:28:50.419673	playing
24	3338914D	블루	h	8	t	2025-12-07 09:28:53.328562	playing
25	3338914D	블루	i	9	t	2025-12-07 09:28:56.879206	playing
26	3338914D	블루	j	10	t	2025-12-07 09:29:04.562724	playing
27	3338914D	블루	k	11	t	2025-12-07 09:29:08.749556	playing
28	3338914D	블루	l	12	t	2025-12-07 09:29:12.597865	playing
29	3338914D	화이트	ㄱ	1	t	2025-12-07 09:29:18.461571	playing
30	3338914D	화이트	ㄴ	2	t	2025-12-07 09:29:25.63293	playing
31	3338914D	화이트	ㄷ	3	t	2025-12-07 09:29:30.346129	playing
32	3338914D	화이트	ㄹ	4	t	2025-12-07 09:29:40.330795	playing
33	3338914D	화이트	ㅁ	5	t	2025-12-07 09:29:43.944998	playing
34	3338914D	화이트	ㅂ	6	t	2025-12-07 09:29:48.372397	playing
35	3338914D	화이트	ㅅ	7	t	2025-12-07 09:29:51.893061	playing
36	3338914D	화이트	ㅇ	8	t	2025-12-07 09:29:58.610489	playing
37	3338914D	화이트	ㅈ	9	t	2025-12-07 09:30:02.623113	playing
38	3338914D	화이트	ㅊ	10	t	2025-12-07 09:30:07.53777	playing
39	3338914D	화이트	ㅋ	11	t	2025-12-07 09:30:13.517452	playing
40	3338914D	화이트	ㅌ	12	t	2025-12-07 09:30:22.433	playing
41	3338914D	블루	ㄱ	13	t	2025-12-07 09:37:36.374612	playing
51	6DE3713E	블루	j	6	t	2025-12-09 11:59:15.68049	playing
45	6DE3713E	블루	d	8	t	2025-12-09 11:58:54.098196	playing
47	6DE3713E	블루	f	7	t	2025-12-09 11:59:00.594973	playing
46	6DE3713E	블루	e	3	t	2025-12-09 11:58:57.309512	playing
56	6DE3713E	화이트	o	4	t	2025-12-09 11:59:38.002543	playing
57	6DE3713E	화이트	p	5	t	2025-12-09 11:59:42.161917	playing
58	6DE3713E	화이트	q	6	t	2025-12-09 12:00:04.564874	playing
59	6DE3713E	화이트	r	7	t	2025-12-09 12:00:08.938106	playing
60	6DE3713E	화이트	s	8	t	2025-12-09 12:00:13.862216	playing
61	6DE3713E	화이트	t	9	t	2025-12-09 12:00:17.55916	playing
62	6DE3713E	화이트	u	10	t	2025-12-09 12:00:24.154394	playing
63	6DE3713E	화이트	v	11	t	2025-12-09 12:00:30.351317	playing
55	6DE3713E	화이트	n	1	t	2025-12-09 11:59:33.913233	playing
54	6DE3713E	화이트	m	3	t	2025-12-09 11:59:29.369525	playing
43	6DE3713E	블루	b	2	t	2025-12-09 11:58:48.179955	playing
48	6DE3713E	블루	g	1	t	2025-12-09 11:59:04.517036	playing
66	6DE3713E	블루	cde	14	t	2025-12-10 13:11:15.554295	playing
67	6DE3713E	화이트	xyz	12	t	2025-12-10 13:11:25.060974	playing
49	6DE3713E	블루	h	13	t	2025-12-09 11:59:08.659485	playing
102	8273D3DB	블루	김철희	6	t	2025-12-13 02:21:26.475231	playing
103	8273D3DB	블루	최명수	7	t	2025-12-13 02:21:35.182174	playing
64	6DE3713E	블루	z	9	t	2025-12-09 12:08:35.175405	playing
92	8273D3DB	블루	강현정	3	t	2025-12-12 05:26:02.776531	playing
65	6DE3713E	블루	abc	11	t	2025-12-10 13:11:12.46297	playing
50	6DE3713E	블루	i	10	t	2025-12-09 11:59:12.561332	playing
68	B6189566	블루	asdas	1	t	2025-12-10 13:17:59.237487	playing
52	6DE3713E	블루	k	12	t	2025-12-09 11:59:19.384939	playing
69	B6189566	블루	b	2	t	2025-12-10 13:18:02.542644	playing
70	B6189566	블루	c	3	t	2025-12-10 13:18:04.022153	playing
71	B6189566	블루	d	4	t	2025-12-10 13:18:05.266616	playing
72	B6189566	블루	e	5	t	2025-12-10 13:18:08.071883	playing
73	B6189566	화이트	f	1	t	2025-12-10 13:18:10.045143	playing
74	B6189566	화이트	g	2	t	2025-12-10 13:18:12.086653	playing
75	B6189566	화이트	h	3	t	2025-12-10 13:18:13.270799	playing
76	B6189566	화이트	i	4	t	2025-12-10 13:18:14.620289	playing
77	B6189566	화이트	j	5	t	2025-12-10 13:18:18.172938	playing
53	6DE3713E	화이트	l	2	t	2025-12-09 11:59:25.725119	playing
83	B4EC16C0	블루	b	3	t	2025-12-10 13:58:26.894933	playing
84	B4EC16C0	블루	c	4	t	2025-12-10 13:58:28.397769	playing
89	B4EC16C0	블루	f	5	t	2025-12-10 13:58:53.690728	playing
85	B4EC16C0	화이트	d	2	t	2025-12-10 13:58:32.62197	playing
87	B4EC16C0	화이트	f	4	t	2025-12-10 13:58:36.120734	playing
88	B4EC16C0	화이트	g	5	t	2025-12-10 13:58:37.549633	playing
82	B4EC16C0	화이트	a	1	t	2025-12-10 13:58:26.063912	playing
80	B4EC16C0	블루	원동현	2	t	2025-12-10 13:58:04.644698	playing
86	B4EC16C0	블루	e	1	t	2025-12-10 13:58:33.19659	playing
78	B4EC16C0	화이트	임수암	3	t	2025-12-10 13:57:53.320068	playing
90	75A46682	화이트	감두희	1	t	2025-12-12 02:37:29.000001	playing
44	6DE3713E	블루	c	4	t	2025-12-09 11:58:51.448693	playing
42	6DE3713E	블루	a	5	t	2025-12-09 11:58:44.839133	playing
98	8273D3DB	블루	ㄴ	1	t	2025-12-12 05:26:29.932717	playing
100	8273D3DB	블루	ㄹ	4	t	2025-12-12 05:26:32.378012	playing
93	8273D3DB	블루	감두희	2	t	2025-12-12 05:26:10.365926	bench
91	8273D3DB	블루	원동현	5	t	2025-12-12 05:25:53.074993	bench
95	8273D3DB	화이트	아무개	1	t	2025-12-12 05:26:19.702226	playing
96	8273D3DB	화이트	ㅁ	3	t	2025-12-12 05:26:21.165145	playing
97	8273D3DB	화이트	ㄱ	5	t	2025-12-12 05:26:28.883061	playing
99	8273D3DB	화이트	ㄷ	2	t	2025-12-12 05:26:31.119688	playing
101	8273D3DB	화이트	ㅂ	4	t	2025-12-12 05:26:40.092186	playing
\.


--
-- Data for Name: quarters; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.quarters (id, game_id, quarter_number, status, playing_blue, playing_white, bench_blue, bench_white, score_blue, score_white, started_at, ended_at, lineup_snapshot) FROM stdin;
1	F606932F	1	종료	[1, 2, 3, 4, 5]	[1, 2, 3, 4, 5]	[6, 7, 8]	[6, 7]	0	0	2025-12-07 09:24:25.323494	2025-12-07 09:25:02.265418	\N
2	F606932F	2	종료	[8, 7, 6, 1, 2]	[7, 6, 1, 2, 3]	[3, 4, 5]	[4, 5]	0	0	2025-12-07 09:25:20.224578	2025-12-07 09:26:40.282488	\N
3	F606932F	3	진행중	[5, 4, 3, 8, 7]	[5, 4, 7, 6, 1]	[6, 1, 2]	[2, 3]	0	0	2025-12-07 09:26:47.160435	\N	\N
17	8273D3DB	1	종료	[1, 2, 3, 5, 6]	[1, 2, 3, 5, 4]	[4]	[]	12	15	2025-12-12 14:40:49.242009	2025-12-12 14:41:02.345911	{"\\ube14\\ub8e8": {"4": "\\uc6d0\\ub3d9\\ud604", "3": "\\uc784\\uc218\\uc554", "5": "\\u3137", "6": "\\u3141", "1": "\\uc544\\ubb34\\uac1c", "2": "\\u3139"}, "\\ud654\\uc774\\ud2b8": {"1": "\\uac15\\ud604\\uc815", "5": "\\u3134", "4": "\\u3131", "3": "\\uac10\\ub450\\ud76c", "2": "\\u3142"}}
4	3338914D	1	종료	[1, 2, 3, 4, 5]	[1, 2, 3, 4, 5]	[6, 7, 8, 9, 10, 11, 12]	[6, 7, 8, 9, 10, 11, 12]	10	15	2025-12-07 09:30:42.459095	2025-12-07 09:30:50.472004	\N
13	B4EC16C0	1	종료	[1, 4, 3, 2, 6]	[2, 1, 5, 3, 6]	[5]	[4]	10	12	2025-12-10 13:59:48.487182	2025-12-10 14:00:09.564342	{"\\ube14\\ub8e8": {"1": "\\uc784\\uc218\\uc554", "2": "\\uac10\\ub450\\ud76c", "3": "a", "4": "b", "5": "c", "6": "f"}, "\\ud654\\uc774\\ud2b8": {"1": "\\uac15\\ud604\\uc815", "2": "\\uc6d0\\ub3d9\\ud604", "3": "d", "4": "e", "5": "f", "6": "g"}}
5	3338914D	2	종료	[12, 11, 10, 9, 8]	[12, 11, 10, 9, 8]	[7, 6, 1, 2, 3, 4, 5]	[7, 6, 1, 2, 3, 4, 5]	20	28	2025-12-07 09:31:19.400046	2025-12-07 09:32:46.854388	\N
6	3338914D	3	종료	[5, 4, 3, 2, 1]	[5, 4, 3, 2, 1]	[6, 7, 12, 11, 10, 9, 8]	[6, 7, 12, 11, 10, 9, 8]	10	12	2025-12-07 09:34:27.496033	2025-12-07 09:34:53.16066	\N
7	3338914D	4	종료	[8, 9, 10, 11, 12]	[8, 9, 10, 11, 12]	[7, 6, 5, 4, 3, 2, 1]	[7, 6, 5, 4, 3, 2, 1]	10	5	2025-12-07 09:35:00.461375	2025-12-07 09:35:17.340473	\N
14	B4EC16C0	2	종료	[1, 2, 3, 4, 5]	[1, 2, 4, 3, 6]	[]	[5]	22	32	2025-12-10 14:06:56.482709	2025-12-10 14:07:15.725108	{"\\ube14\\ub8e8": {"1": "\\uc784\\uc218\\uc554", "2": "a", "3": "b", "4": "c", "5": "f"}, "\\ud654\\uc774\\ud2b8": {"1": "\\uac15\\ud604\\uc815", "2": "\\uc6d0\\ub3d9\\ud604", "3": "d", "4": "e", "5": "f", "6": "g"}}
8	6DE3713E	1	종료	[1, 2, 3, 9, 11]	[1, 2, 3, 4, 5]	[7, 10, 6, 8, 4, 5]	[6, 7, 8, 9, 10, 11]	4	4	2025-12-09 12:04:38.864865	2025-12-09 12:06:33.653542	\N
20	8273D3DB	4	진행중	[1, 4, 6, 7, 3]	[1, 2, 3, 4, 5]	[2, 5]	[]	0	0	2025-12-13 02:22:10.223575	\N	{"\\ube14\\ub8e8": {"6": "\\uae40\\ucca0\\ud76c", "7": "\\ucd5c\\uba85\\uc218", "3": "\\uac15\\ud604\\uc815", "1": "\\u3134", "4": "\\u3139", "2": "\\uac10\\ub450\\ud76c", "5": "\\uc6d0\\ub3d9\\ud604"}, "\\ud654\\uc774\\ud2b8": {"1": "\\uc544\\ubb34\\uac1c", "3": "\\u3141", "5": "\\u3131", "2": "\\u3137", "4": "\\u3142"}}
9	6DE3713E	2	종료	[2, 12, 5, 4, 6]	[1, 3, 5, 7, 9]	[3, 8, 9, 10, 11, 1, 7]	[2, 4, 6, 8, 10, 11]	3	3	2025-12-10 12:46:33.041601	2025-12-10 12:48:16.108845	{"\\ube14\\ub8e8": {"6": "j", "8": "d", "7": "f", "10": "z", "9": "h", "12": "k", "11": "i", "1": "b", "2": "g", "4": "c", "3": "e", "5": "a"}, "\\ud654\\uc774\\ud2b8": {"3": "n", "4": "o", "5": "p", "6": "q", "7": "r", "8": "s", "9": "t", "10": "u", "11": "v", "2": "l", "1": "m"}}
10	6DE3713E	3	종료	[1, 2, 3, 4, 6]	[1, 3, 6, 10, 8]	[5, 7, 8, 9, 10, 11, 12]	[2, 4, 5, 7, 9, 11]	0	0	2025-12-10 13:05:50.421408	2025-12-10 13:06:00.359049	{"\\ube14\\ub8e8": {"6": "j", "8": "d", "7": "f", "3": "e", "1": "b", "2": "g", "10": "z", "9": "h", "12": "k", "11": "i", "4": "c", "5": "a"}, "\\ud654\\uc774\\ud2b8": {"4": "o", "5": "p", "6": "q", "7": "r", "8": "s", "9": "t", "10": "u", "11": "v", "1": "n", "3": "m", "2": "l"}}
11	6DE3713E	4	종료	[14, 13, 3, 5, 7]	[12, 2, 8, 10, 7]	[1, 2, 4, 6, 8, 9, 10, 11, 12]	[1, 3, 4, 5, 6, 9, 11]	0	0	2025-12-10 13:11:52.123217	2025-12-10 13:12:02.931563	{"\\ube14\\ub8e8": {"6": "j", "8": "d", "7": "f", "3": "e", "2": "b", "1": "g", "13": "abc", "10": "z", "14": "cde", "9": "h", "12": "k", "11": "i", "4": "c", "5": "a"}, "\\ud654\\uc774\\ud2b8": {"4": "o", "5": "p", "6": "q", "7": "r", "8": "s", "9": "t", "10": "u", "11": "v", "1": "n", "3": "m", "12": "xyz", "2": "l"}}
12	B6189566	1	종료	[1, 3, 2, 4, 5]	[1, 3, 2, 4, 5]	[]	[]	0	0	2025-12-10 13:18:29.991414	2025-12-10 13:36:29.043112	{"\\ube14\\ub8e8": {"1": "asdas", "2": "b", "3": "c", "4": "d", "5": "e"}, "\\ud654\\uc774\\ud2b8": {"1": "f", "2": "g", "3": "h", "4": "i", "5": "j"}}
15	B4EC16C0	3	종료	[1, 2, 3, 4, 5]	[1, 2, 3, 4, 5]	[]	[]	42	50	2025-12-10 14:07:41.313134	2025-12-10 14:07:54.185203	{"\\ube14\\ub8e8": {"1": "\\uc784\\uc218\\uc554", "2": "a", "3": "b", "4": "c", "5": "f"}, "\\ud654\\uc774\\ud2b8": {"1": "\\uc6d0\\ub3d9\\ud604", "2": "d", "3": "e", "4": "f", "5": "g"}}
16	B4EC16C0	4	종료	[1, 2, 3, 4, 5]	[1, 2, 3, 4, 5]	[]	[]	52	60	2025-12-10 14:08:31.59325	2025-12-10 14:08:44.121264	{"\\ube14\\ub8e8": {"3": "b", "4": "c", "5": "f", "2": "\\uc6d0\\ub3d9\\ud604", "1": "e"}, "\\ud654\\uc774\\ud2b8": {"2": "d", "4": "f", "5": "g", "1": "a", "3": "\\uc784\\uc218\\uc554"}}
18	8273D3DB	2	종료	[2, 3, 5, 4, 1]	[1, 2, 3, 4, 5]	[]	[6]	20	23	2025-12-12 14:42:21.6307	2025-12-12 15:18:52.926799	{"\\ube14\\ub8e8": {"5": "\\uc6d0\\ub3d9\\ud604", "4": "\\uc784\\uc218\\uc554", "2": "\\uc544\\ubb34\\uac1c", "1": "\\u3134", "3": "\\u3139"}, "\\ud654\\uc774\\ud2b8": {"3": "\\uac15\\ud604\\uc815", "5": "\\uac10\\ub450\\ud76c", "2": "\\u3141", "1": "\\u3137", "4": "\\u3142", "6": "\\u3131"}}
19	8273D3DB	3	종료	[1, 5, 2, 3, 4]	[1, 2, 3, 5, 4]	[]	[]	44	42	2025-12-12 15:28:22.302566	2025-12-13 02:21:00.407162	{"\\ube14\\ub8e8": {"1": "\\uac15\\ud604\\uc815", "3": "\\uc544\\ubb34\\uac1c", "2": "\\u3134", "4": "\\u3139", "5": "\\uc6d0\\ub3d9\\ud604"}, "\\ud654\\uc774\\ud2b8": {"4": "\\uac10\\ub450\\ud76c", "2": "\\u3141", "5": "\\u3131", "1": "\\u3137", "3": "\\u3142"}}
\.


--
-- Data for Name: room_members; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.room_members (id, room, name, created_at) FROM stdin;
\.


--
-- Data for Name: rooms; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.rooms (room_id, name, created_at) FROM stdin;
3A92DCDD	원동현	2025-12-07 06:33:47.126777
5D8CB2B6	DEBUG ROOM	2025-12-12 04:55:29.090358
\.


--
-- Name: lineups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.lineups_id_seq', 103, true);


--
-- Name: quarters_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.quarters_id_seq', 20, true);


--
-- Name: room_members_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.room_members_id_seq', 1, false);


--
-- Name: games games_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.games
    ADD CONSTRAINT games_pkey PRIMARY KEY (game_id);


--
-- Name: lineups lineups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lineups
    ADD CONSTRAINT lineups_pkey PRIMARY KEY (id);


--
-- Name: quarters quarters_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quarters
    ADD CONSTRAINT quarters_pkey PRIMARY KEY (id);


--
-- Name: room_members room_members_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_members
    ADD CONSTRAINT room_members_pkey PRIMARY KEY (id);


--
-- Name: rooms rooms_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rooms
    ADD CONSTRAINT rooms_name_key UNIQUE (name);


--
-- Name: rooms rooms_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rooms
    ADD CONSTRAINT rooms_pkey PRIMARY KEY (room_id);


--
-- Name: lineups unique_lineup; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lineups
    ADD CONSTRAINT unique_lineup UNIQUE (game_id, team, number);


--
-- Name: quarters unique_quarter; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quarters
    ADD CONSTRAINT unique_quarter UNIQUE (game_id, quarter_number);


--
-- Name: room_members unique_room_member; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.room_members
    ADD CONSTRAINT unique_room_member UNIQUE (room, name);


--
-- Name: idx_games_room_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_games_room_id ON public.games USING btree (room_id);


--
-- Name: idx_lineup_game_team; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_lineup_game_team ON public.lineups USING btree (game_id, team);


--
-- Name: idx_quarter_game; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_quarter_game ON public.quarters USING btree (game_id);


--
-- Name: idx_room_member_room; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_room_member_room ON public.room_members USING btree (room);


--
-- Name: games fk_games_room_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.games
    ADD CONSTRAINT fk_games_room_id FOREIGN KEY (room_id) REFERENCES public.rooms(room_id) ON DELETE CASCADE;


--
-- Name: lineups lineups_game_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lineups
    ADD CONSTRAINT lineups_game_id_fkey FOREIGN KEY (game_id) REFERENCES public.games(game_id) ON DELETE CASCADE;


--
-- Name: quarters quarters_game_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quarters
    ADD CONSTRAINT quarters_game_id_fkey FOREIGN KEY (game_id) REFERENCES public.games(game_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict fjHMNtqmKzuysmyS6F46H9W1z0bvPcbuTtL49zfODVpfPh8WgIyX9mUQzciHszI

