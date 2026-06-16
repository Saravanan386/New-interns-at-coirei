--
-- PostgreSQL database dump
--

\restrict mWSJWcdTdfVlnZnQyZkTnsoT1yvtmwvDtdDgOmMbTF7PEaBLIoOqTNWefFE7MDj

-- Dumped from database version 17.8 (ad62774)
-- Dumped by pg_dump version 18.1

-- Started on 2026-05-11 14:12:08

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
-- TOC entry 254 (class 1259 OID 139285)
-- Name: assignment_resources; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.assignment_resources (
    id integer NOT NULL,
    assignment_id integer NOT NULL,
    file_name character varying NOT NULL,
    file_path character varying NOT NULL,
    file_type character varying,
    uploaded_at timestamp without time zone
);


ALTER TABLE public.assignment_resources OWNER TO neondb_owner;

--
-- TOC entry 253 (class 1259 OID 139284)
-- Name: assignment_resources_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.assignment_resources_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.assignment_resources_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3809 (class 0 OID 0)
-- Dependencies: 253
-- Name: assignment_resources_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.assignment_resources_id_seq OWNED BY public.assignment_resources.id;


--
-- TOC entry 256 (class 1259 OID 139300)
-- Name: assignment_submissions; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.assignment_submissions (
    id integer NOT NULL,
    assignment_id integer NOT NULL,
    student_user_id integer NOT NULL,
    submission_text text,
    file_path character varying,
    file_name character varying,
    submitted_at timestamp without time zone,
    status character varying,
    grade character varying,
    feedback text
);


ALTER TABLE public.assignment_submissions OWNER TO neondb_owner;

--
-- TOC entry 255 (class 1259 OID 139299)
-- Name: assignment_submissions_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.assignment_submissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.assignment_submissions_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3810 (class 0 OID 0)
-- Dependencies: 255
-- Name: assignment_submissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.assignment_submissions_id_seq OWNED BY public.assignment_submissions.id;


--
-- TOC entry 252 (class 1259 OID 139265)
-- Name: assignments; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.assignments (
    id integer NOT NULL,
    course_id integer NOT NULL,
    batch_name character varying NOT NULL,
    module_name character varying NOT NULL,
    title character varying NOT NULL,
    description text,
    expected_outcome text,
    due_date timestamp without time zone,
    created_by integer NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.assignments OWNER TO neondb_owner;

--
-- TOC entry 251 (class 1259 OID 139264)
-- Name: assignments_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.assignments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.assignments_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3811 (class 0 OID 0)
-- Dependencies: 251
-- Name: assignments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.assignments_id_seq OWNED BY public.assignments.id;


--
-- TOC entry 238 (class 1259 OID 98350)
-- Name: assignments_module; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.assignments_module (
    id integer NOT NULL,
    title character varying NOT NULL,
    due_date timestamp without time zone,
    module_id integer NOT NULL
);


ALTER TABLE public.assignments_module OWNER TO neondb_owner;

--
-- TOC entry 237 (class 1259 OID 98349)
-- Name: assignments_module_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.assignments_module_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.assignments_module_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3812 (class 0 OID 0)
-- Dependencies: 237
-- Name: assignments_module_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.assignments_module_id_seq OWNED BY public.assignments_module.id;


--
-- TOC entry 234 (class 1259 OID 98320)
-- Name: chapters; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.chapters (
    id integer NOT NULL,
    title character varying NOT NULL,
    "order" integer,
    module_id integer NOT NULL
);


ALTER TABLE public.chapters OWNER TO neondb_owner;

--
-- TOC entry 233 (class 1259 OID 98319)
-- Name: chapters_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.chapters_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.chapters_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3813 (class 0 OID 0)
-- Dependencies: 233
-- Name: chapters_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.chapters_id_seq OWNED BY public.chapters.id;


--
-- TOC entry 264 (class 1259 OID 147515)
-- Name: chat_bookmarks; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.chat_bookmarks (
    id integer NOT NULL,
    post_id integer NOT NULL,
    user_id integer NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.chat_bookmarks OWNER TO neondb_owner;

--
-- TOC entry 263 (class 1259 OID 147514)
-- Name: chat_bookmarks_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.chat_bookmarks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.chat_bookmarks_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3814 (class 0 OID 0)
-- Dependencies: 263
-- Name: chat_bookmarks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.chat_bookmarks_id_seq OWNED BY public.chat_bookmarks.id;


--
-- TOC entry 262 (class 1259 OID 147497)
-- Name: chat_likes; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.chat_likes (
    id integer NOT NULL,
    post_id integer NOT NULL,
    user_id integer NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.chat_likes OWNER TO neondb_owner;

--
-- TOC entry 261 (class 1259 OID 147496)
-- Name: chat_likes_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.chat_likes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.chat_likes_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3815 (class 0 OID 0)
-- Dependencies: 261
-- Name: chat_likes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.chat_likes_id_seq OWNED BY public.chat_likes.id;


--
-- TOC entry 258 (class 1259 OID 147457)
-- Name: chat_posts; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.chat_posts (
    id integer NOT NULL,
    course_id integer NOT NULL,
    batch_name character varying NOT NULL,
    author_id integer NOT NULL,
    author_role character varying NOT NULL,
    content text NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    is_pinned boolean,
    pinned_at timestamp without time zone
);


ALTER TABLE public.chat_posts OWNER TO neondb_owner;

--
-- TOC entry 257 (class 1259 OID 147456)
-- Name: chat_posts_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.chat_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.chat_posts_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3816 (class 0 OID 0)
-- Dependencies: 257
-- Name: chat_posts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.chat_posts_id_seq OWNED BY public.chat_posts.id;


--
-- TOC entry 260 (class 1259 OID 147477)
-- Name: chat_replies; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.chat_replies (
    id integer NOT NULL,
    post_id integer NOT NULL,
    author_id integer NOT NULL,
    author_role character varying NOT NULL,
    content text NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.chat_replies OWNER TO neondb_owner;

--
-- TOC entry 259 (class 1259 OID 147476)
-- Name: chat_replies_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.chat_replies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.chat_replies_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3817 (class 0 OID 0)
-- Dependencies: 259
-- Name: chat_replies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.chat_replies_id_seq OWNED BY public.chat_replies.id;


--
-- TOC entry 270 (class 1259 OID 188417)
-- Name: chat_reply_likes; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.chat_reply_likes (
    id integer NOT NULL,
    reply_id integer NOT NULL,
    user_id integer NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.chat_reply_likes OWNER TO neondb_owner;

--
-- TOC entry 269 (class 1259 OID 188416)
-- Name: chat_reply_likes_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.chat_reply_likes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.chat_reply_likes_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3818 (class 0 OID 0)
-- Dependencies: 269
-- Name: chat_reply_likes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.chat_reply_likes_id_seq OWNED BY public.chat_reply_likes.id;


--
-- TOC entry 217 (class 1259 OID 40972)
-- Name: class_sessions; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.class_sessions (
    id integer NOT NULL,
    classroom_id integer,
    start_time timestamp without time zone,
    end_time timestamp without time zone,
    status character varying,
    join_url text,
    course_id integer,
    batch_name character varying(100),
    livekit_room_name character varying,
    host_url character varying,
    egress_id character varying
);


ALTER TABLE public.class_sessions OWNER TO neondb_owner;

--
-- TOC entry 218 (class 1259 OID 40977)
-- Name: class_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.class_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.class_sessions_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3819 (class 0 OID 0)
-- Dependencies: 218
-- Name: class_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.class_sessions_id_seq OWNED BY public.class_sessions.id;


--
-- TOC entry 219 (class 1259 OID 40978)
-- Name: classrooms; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.classrooms (
    id integer NOT NULL,
    course_name character varying,
    batch_name character varying,
    room_name character varying,
    course_id integer
);


ALTER TABLE public.classrooms OWNER TO neondb_owner;

--
-- TOC entry 220 (class 1259 OID 40983)
-- Name: classrooms_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.classrooms_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.classrooms_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3820 (class 0 OID 0)
-- Dependencies: 220
-- Name: classrooms_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.classrooms_id_seq OWNED BY public.classrooms.id;


--
-- TOC entry 230 (class 1259 OID 90113)
-- Name: course_schedules; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.course_schedules (
    id integer NOT NULL,
    course_id integer NOT NULL,
    batch_name character varying NOT NULL,
    day_of_week character varying NOT NULL,
    session_type character varying NOT NULL,
    start_time character varying NOT NULL,
    end_time character varying NOT NULL,
    instructor_name character varying
);


ALTER TABLE public.course_schedules OWNER TO neondb_owner;

--
-- TOC entry 229 (class 1259 OID 90112)
-- Name: course_schedules_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.course_schedules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.course_schedules_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3821 (class 0 OID 0)
-- Dependencies: 229
-- Name: course_schedules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.course_schedules_id_seq OWNED BY public.course_schedules.id;


--
-- TOC entry 221 (class 1259 OID 40984)
-- Name: courses; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.courses (
    id integer NOT NULL,
    name character varying NOT NULL,
    duration_months integer,
    total_lessons integer
);


ALTER TABLE public.courses OWNER TO neondb_owner;

--
-- TOC entry 222 (class 1259 OID 40989)
-- Name: courses_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.courses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.courses_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3822 (class 0 OID 0)
-- Dependencies: 222
-- Name: courses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.courses_id_seq OWNED BY public.courses.id;


--
-- TOC entry 272 (class 1259 OID 188435)
-- Name: dm_conversations; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.dm_conversations (
    id integer NOT NULL,
    user_a_id integer NOT NULL,
    user_b_id integer NOT NULL,
    unread_a integer,
    unread_b integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.dm_conversations OWNER TO neondb_owner;

--
-- TOC entry 271 (class 1259 OID 188434)
-- Name: dm_conversations_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.dm_conversations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dm_conversations_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3823 (class 0 OID 0)
-- Dependencies: 271
-- Name: dm_conversations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.dm_conversations_id_seq OWNED BY public.dm_conversations.id;


--
-- TOC entry 282 (class 1259 OID 188532)
-- Name: dm_message_bookmarks; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.dm_message_bookmarks (
    id integer NOT NULL,
    message_id integer NOT NULL,
    user_id integer NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.dm_message_bookmarks OWNER TO neondb_owner;

--
-- TOC entry 281 (class 1259 OID 188531)
-- Name: dm_message_bookmarks_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.dm_message_bookmarks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dm_message_bookmarks_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3824 (class 0 OID 0)
-- Dependencies: 281
-- Name: dm_message_bookmarks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.dm_message_bookmarks_id_seq OWNED BY public.dm_message_bookmarks.id;


--
-- TOC entry 280 (class 1259 OID 188512)
-- Name: dm_message_likes; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.dm_message_likes (
    id integer NOT NULL,
    message_id integer NOT NULL,
    user_id integer NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.dm_message_likes OWNER TO neondb_owner;

--
-- TOC entry 279 (class 1259 OID 188511)
-- Name: dm_message_likes_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.dm_message_likes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dm_message_likes_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3825 (class 0 OID 0)
-- Dependencies: 279
-- Name: dm_message_likes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.dm_message_likes_id_seq OWNED BY public.dm_message_likes.id;


--
-- TOC entry 276 (class 1259 OID 188472)
-- Name: dm_messages; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.dm_messages (
    id integer NOT NULL,
    conversation_id integer NOT NULL,
    sender_id integer NOT NULL,
    text text,
    attachment_url character varying,
    attachment_name character varying,
    created_at timestamp without time zone,
    deleted_at timestamp without time zone
);


ALTER TABLE public.dm_messages OWNER TO neondb_owner;

--
-- TOC entry 275 (class 1259 OID 188471)
-- Name: dm_messages_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.dm_messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dm_messages_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3826 (class 0 OID 0)
-- Dependencies: 275
-- Name: dm_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.dm_messages_id_seq OWNED BY public.dm_messages.id;


--
-- TOC entry 223 (class 1259 OID 40990)
-- Name: enrollments; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.enrollments (
    id integer NOT NULL,
    user_id integer NOT NULL,
    course_id integer NOT NULL,
    progress_percent integer DEFAULT 0,
    status character varying DEFAULT 'ongoing'::character varying,
    classroom_id integer,
    batch_name character varying
);


ALTER TABLE public.enrollments OWNER TO neondb_owner;

--
-- TOC entry 224 (class 1259 OID 40997)
-- Name: enrollments_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.enrollments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.enrollments_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3827 (class 0 OID 0)
-- Dependencies: 224
-- Name: enrollments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.enrollments_id_seq OWNED BY public.enrollments.id;


--
-- TOC entry 274 (class 1259 OID 188455)
-- Name: group_chats; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.group_chats (
    id integer NOT NULL,
    course_id integer NOT NULL,
    batch_name character varying NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.group_chats OWNER TO neondb_owner;

--
-- TOC entry 273 (class 1259 OID 188454)
-- Name: group_chats_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.group_chats_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.group_chats_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3828 (class 0 OID 0)
-- Dependencies: 273
-- Name: group_chats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.group_chats_id_seq OWNED BY public.group_chats.id;


--
-- TOC entry 286 (class 1259 OID 188572)
-- Name: group_message_bookmarks; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.group_message_bookmarks (
    id integer NOT NULL,
    message_id integer NOT NULL,
    user_id integer NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.group_message_bookmarks OWNER TO neondb_owner;

--
-- TOC entry 285 (class 1259 OID 188571)
-- Name: group_message_bookmarks_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.group_message_bookmarks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.group_message_bookmarks_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3829 (class 0 OID 0)
-- Dependencies: 285
-- Name: group_message_bookmarks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.group_message_bookmarks_id_seq OWNED BY public.group_message_bookmarks.id;


--
-- TOC entry 284 (class 1259 OID 188552)
-- Name: group_message_likes; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.group_message_likes (
    id integer NOT NULL,
    message_id integer NOT NULL,
    user_id integer NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.group_message_likes OWNER TO neondb_owner;

--
-- TOC entry 283 (class 1259 OID 188551)
-- Name: group_message_likes_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.group_message_likes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.group_message_likes_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3830 (class 0 OID 0)
-- Dependencies: 283
-- Name: group_message_likes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.group_message_likes_id_seq OWNED BY public.group_message_likes.id;


--
-- TOC entry 278 (class 1259 OID 188492)
-- Name: group_messages; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.group_messages (
    id integer NOT NULL,
    group_id integer NOT NULL,
    sender_id integer NOT NULL,
    sender_role character varying NOT NULL,
    text text,
    attachment_url character varying,
    attachment_name character varying,
    is_pinned boolean,
    pinned_at timestamp without time zone,
    created_at timestamp without time zone,
    deleted_at timestamp without time zone
);


ALTER TABLE public.group_messages OWNER TO neondb_owner;

--
-- TOC entry 277 (class 1259 OID 188491)
-- Name: group_messages_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.group_messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.group_messages_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3831 (class 0 OID 0)
-- Dependencies: 277
-- Name: group_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.group_messages_id_seq OWNED BY public.group_messages.id;


--
-- TOC entry 268 (class 1259 OID 180225)
-- Name: instructor_enrollments; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.instructor_enrollments (
    id integer NOT NULL,
    user_id integer NOT NULL,
    course_id integer NOT NULL,
    batch_name character varying NOT NULL
);


ALTER TABLE public.instructor_enrollments OWNER TO neondb_owner;

--
-- TOC entry 267 (class 1259 OID 180224)
-- Name: instructor_enrollments_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.instructor_enrollments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.instructor_enrollments_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3832 (class 0 OID 0)
-- Dependencies: 267
-- Name: instructor_enrollments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.instructor_enrollments_id_seq OWNED BY public.instructor_enrollments.id;


--
-- TOC entry 232 (class 1259 OID 98305)
-- Name: modules; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.modules (
    id integer NOT NULL,
    title character varying NOT NULL,
    "order" integer,
    status character varying,
    course_id integer NOT NULL,
    batch_name character varying
);


ALTER TABLE public.modules OWNER TO neondb_owner;

--
-- TOC entry 231 (class 1259 OID 98304)
-- Name: modules_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.modules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.modules_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3833 (class 0 OID 0)
-- Dependencies: 231
-- Name: modules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.modules_id_seq OWNED BY public.modules.id;


--
-- TOC entry 266 (class 1259 OID 172033)
-- Name: notifications; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.notifications (
    id integer NOT NULL,
    user_id integer NOT NULL,
    type character varying NOT NULL,
    title character varying NOT NULL,
    message character varying NOT NULL,
    is_read boolean NOT NULL,
    created_at timestamp without time zone,
    related_id integer
);


ALTER TABLE public.notifications OWNER TO neondb_owner;

--
-- TOC entry 265 (class 1259 OID 172032)
-- Name: notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notifications_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3834 (class 0 OID 0)
-- Dependencies: 265
-- Name: notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.notifications_id_seq OWNED BY public.notifications.id;


--
-- TOC entry 246 (class 1259 OID 122911)
-- Name: question_options; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.question_options (
    id integer NOT NULL,
    question_id integer NOT NULL,
    text character varying NOT NULL,
    is_correct boolean
);


ALTER TABLE public.question_options OWNER TO neondb_owner;

--
-- TOC entry 245 (class 1259 OID 122910)
-- Name: question_options_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.question_options_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.question_options_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3835 (class 0 OID 0)
-- Dependencies: 245
-- Name: question_options_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.question_options_id_seq OWNED BY public.question_options.id;


--
-- TOC entry 236 (class 1259 OID 98335)
-- Name: resources_module; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.resources_module (
    id integer NOT NULL,
    title character varying NOT NULL,
    file_url character varying,
    module_id integer NOT NULL
);


ALTER TABLE public.resources_module OWNER TO neondb_owner;

--
-- TOC entry 235 (class 1259 OID 98334)
-- Name: resources_module_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.resources_module_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.resources_module_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3836 (class 0 OID 0)
-- Dependencies: 235
-- Name: resources_module_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.resources_module_id_seq OWNED BY public.resources_module.id;


--
-- TOC entry 225 (class 1259 OID 40998)
-- Name: session_participants; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.session_participants (
    id integer NOT NULL,
    session_id integer,
    user_id integer,
    join_time timestamp without time zone,
    leave_time timestamp without time zone,
    duration_minutes double precision,
    status character varying
);


ALTER TABLE public.session_participants OWNER TO neondb_owner;

--
-- TOC entry 226 (class 1259 OID 41003)
-- Name: session_participants_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.session_participants_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.session_participants_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3837 (class 0 OID 0)
-- Dependencies: 226
-- Name: session_participants_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.session_participants_id_seq OWNED BY public.session_participants.id;


--
-- TOC entry 250 (class 1259 OID 131093)
-- Name: student_answers; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.student_answers (
    id integer NOT NULL,
    submission_id integer NOT NULL,
    question_id integer NOT NULL,
    selected_option_id integer
);


ALTER TABLE public.student_answers OWNER TO neondb_owner;

--
-- TOC entry 249 (class 1259 OID 131092)
-- Name: student_answers_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.student_answers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.student_answers_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3838 (class 0 OID 0)
-- Dependencies: 249
-- Name: student_answers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.student_answers_id_seq OWNED BY public.student_answers.id;


--
-- TOC entry 244 (class 1259 OID 122896)
-- Name: test_questions; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.test_questions (
    id integer NOT NULL,
    test_id integer NOT NULL,
    text character varying NOT NULL
);


ALTER TABLE public.test_questions OWNER TO neondb_owner;

--
-- TOC entry 243 (class 1259 OID 122895)
-- Name: test_questions_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.test_questions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.test_questions_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3839 (class 0 OID 0)
-- Dependencies: 243
-- Name: test_questions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.test_questions_id_seq OWNED BY public.test_questions.id;


--
-- TOC entry 248 (class 1259 OID 131073)
-- Name: test_submissions; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.test_submissions (
    id integer NOT NULL,
    test_id integer NOT NULL,
    student_user_id integer NOT NULL,
    started_at timestamp without time zone,
    submitted_at timestamp without time zone,
    score double precision,
    is_passed boolean,
    status character varying
);


ALTER TABLE public.test_submissions OWNER TO neondb_owner;

--
-- TOC entry 247 (class 1259 OID 131072)
-- Name: test_submissions_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.test_submissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.test_submissions_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3840 (class 0 OID 0)
-- Dependencies: 247
-- Name: test_submissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.test_submissions_id_seq OWNED BY public.test_submissions.id;


--
-- TOC entry 242 (class 1259 OID 122881)
-- Name: tests; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.tests (
    id integer NOT NULL,
    title character varying NOT NULL,
    description character varying,
    course_id integer NOT NULL,
    batch_name character varying NOT NULL,
    module_name character varying NOT NULL,
    start_time timestamp without time zone,
    end_time timestamp without time zone,
    created_at timestamp without time zone
);


ALTER TABLE public.tests OWNER TO neondb_owner;

--
-- TOC entry 241 (class 1259 OID 122880)
-- Name: tests_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.tests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tests_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3841 (class 0 OID 0)
-- Dependencies: 241
-- Name: tests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.tests_id_seq OWNED BY public.tests.id;


--
-- TOC entry 240 (class 1259 OID 98365)
-- Name: tests_module; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.tests_module (
    id integer NOT NULL,
    title character varying NOT NULL,
    test_date timestamp without time zone,
    module_id integer NOT NULL
);


ALTER TABLE public.tests_module OWNER TO neondb_owner;

--
-- TOC entry 239 (class 1259 OID 98364)
-- Name: tests_module_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.tests_module_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tests_module_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3842 (class 0 OID 0)
-- Dependencies: 239
-- Name: tests_module_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.tests_module_id_seq OWNED BY public.tests_module.id;


--
-- TOC entry 227 (class 1259 OID 41004)
-- Name: users; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.users (
    id integer NOT NULL,
    name character varying NOT NULL,
    email character varying NOT NULL,
    password_hash character varying NOT NULL,
    role character varying NOT NULL,
    student_id character varying
);


ALTER TABLE public.users OWNER TO neondb_owner;

--
-- TOC entry 228 (class 1259 OID 41009)
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO neondb_owner;

--
-- TOC entry 3843 (class 0 OID 0)
-- Dependencies: 228
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- TOC entry 3400 (class 2604 OID 139288)
-- Name: assignment_resources id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.assignment_resources ALTER COLUMN id SET DEFAULT nextval('public.assignment_resources_id_seq'::regclass);


--
-- TOC entry 3401 (class 2604 OID 139303)
-- Name: assignment_submissions id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.assignment_submissions ALTER COLUMN id SET DEFAULT nextval('public.assignment_submissions_id_seq'::regclass);


--
-- TOC entry 3399 (class 2604 OID 139268)
-- Name: assignments id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.assignments ALTER COLUMN id SET DEFAULT nextval('public.assignments_id_seq'::regclass);


--
-- TOC entry 3392 (class 2604 OID 98353)
-- Name: assignments_module id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.assignments_module ALTER COLUMN id SET DEFAULT nextval('public.assignments_module_id_seq'::regclass);


--
-- TOC entry 3390 (class 2604 OID 98323)
-- Name: chapters id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.chapters ALTER COLUMN id SET DEFAULT nextval('public.chapters_id_seq'::regclass);


--
-- TOC entry 3405 (class 2604 OID 147518)
-- Name: chat_bookmarks id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.chat_bookmarks ALTER COLUMN id SET DEFAULT nextval('public.chat_bookmarks_id_seq'::regclass);


--
-- TOC entry 3404 (class 2604 OID 147500)
-- Name: chat_likes id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.chat_likes ALTER COLUMN id SET DEFAULT nextval('public.chat_likes_id_seq'::regclass);


--
-- TOC entry 3402 (class 2604 OID 147460)
-- Name: chat_posts id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.chat_posts ALTER COLUMN id SET DEFAULT nextval('public.chat_posts_id_seq'::regclass);


--
-- TOC entry 3403 (class 2604 OID 147480)
-- Name: chat_replies id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.chat_replies ALTER COLUMN id SET DEFAULT nextval('public.chat_replies_id_seq'::regclass);


--
-- TOC entry 3408 (class 2604 OID 188420)
-- Name: chat_reply_likes id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.chat_reply_likes ALTER COLUMN id SET DEFAULT nextval('public.chat_reply_likes_id_seq'::regclass);


--
-- TOC entry 3380 (class 2604 OID 41010)
-- Name: class_sessions id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.class_sessions ALTER COLUMN id SET DEFAULT nextval('public.class_sessions_id_seq'::regclass);


--
-- TOC entry 3381 (class 2604 OID 41011)
-- Name: classrooms id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.classrooms ALTER COLUMN id SET DEFAULT nextval('public.classrooms_id_seq'::regclass);


--
-- TOC entry 3388 (class 2604 OID 90116)
-- Name: course_schedules id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.course_schedules ALTER COLUMN id SET DEFAULT nextval('public.course_schedules_id_seq'::regclass);


--
-- TOC entry 3382 (class 2604 OID 41012)
-- Name: courses id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.courses ALTER COLUMN id SET DEFAULT nextval('public.courses_id_seq'::regclass);


--
-- TOC entry 3409 (class 2604 OID 188438)
-- Name: dm_conversations id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.dm_conversations ALTER COLUMN id SET DEFAULT nextval('public.dm_conversations_id_seq'::regclass);


--
-- TOC entry 3414 (class 2604 OID 188535)
-- Name: dm_message_bookmarks id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.dm_message_bookmarks ALTER COLUMN id SET DEFAULT nextval('public.dm_message_bookmarks_id_seq'::regclass);


--
-- TOC entry 3413 (class 2604 OID 188515)
-- Name: dm_message_likes id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.dm_message_likes ALTER COLUMN id SET DEFAULT nextval('public.dm_message_likes_id_seq'::regclass);


--
-- TOC entry 3411 (class 2604 OID 188475)
-- Name: dm_messages id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.dm_messages ALTER COLUMN id SET DEFAULT nextval('public.dm_messages_id_seq'::regclass);


--
-- TOC entry 3383 (class 2604 OID 41013)
-- Name: enrollments id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.enrollments ALTER COLUMN id SET DEFAULT nextval('public.enrollments_id_seq'::regclass);


--
-- TOC entry 3410 (class 2604 OID 188458)
-- Name: group_chats id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.group_chats ALTER COLUMN id SET DEFAULT nextval('public.group_chats_id_seq'::regclass);


--
-- TOC entry 3416 (class 2604 OID 188575)
-- Name: group_message_bookmarks id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.group_message_bookmarks ALTER COLUMN id SET DEFAULT nextval('public.group_message_bookmarks_id_seq'::regclass);


--
-- TOC entry 3415 (class 2604 OID 188555)
-- Name: group_message_likes id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.group_message_likes ALTER COLUMN id SET DEFAULT nextval('public.group_message_likes_id_seq'::regclass);


--
-- TOC entry 3412 (class 2604 OID 188495)
-- Name: group_messages id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.group_messages ALTER COLUMN id SET DEFAULT nextval('public.group_messages_id_seq'::regclass);


--
-- TOC entry 3407 (class 2604 OID 180228)
-- Name: instructor_enrollments id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.instructor_enrollments ALTER COLUMN id SET DEFAULT nextval('public.instructor_enrollments_id_seq'::regclass);


--
-- TOC entry 3389 (class 2604 OID 98308)
-- Name: modules id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.modules ALTER COLUMN id SET DEFAULT nextval('public.modules_id_seq'::regclass);


--
-- TOC entry 3406 (class 2604 OID 172036)
-- Name: notifications id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.notifications ALTER COLUMN id SET DEFAULT nextval('public.notifications_id_seq'::regclass);


--
-- TOC entry 3396 (class 2604 OID 122914)
-- Name: question_options id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.question_options ALTER COLUMN id SET DEFAULT nextval('public.question_options_id_seq'::regclass);


--
-- TOC entry 3391 (class 2604 OID 98338)
-- Name: resources_module id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.resources_module ALTER COLUMN id SET DEFAULT nextval('public.resources_module_id_seq'::regclass);


--
-- TOC entry 3386 (class 2604 OID 41014)
-- Name: session_participants id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.session_participants ALTER COLUMN id SET DEFAULT nextval('public.session_participants_id_seq'::regclass);


--
-- TOC entry 3398 (class 2604 OID 131096)
-- Name: student_answers id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.student_answers ALTER COLUMN id SET DEFAULT nextval('public.student_answers_id_seq'::regclass);


--
-- TOC entry 3395 (class 2604 OID 122899)
-- Name: test_questions id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.test_questions ALTER COLUMN id SET DEFAULT nextval('public.test_questions_id_seq'::regclass);


--
-- TOC entry 3397 (class 2604 OID 131076)
-- Name: test_submissions id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.test_submissions ALTER COLUMN id SET DEFAULT nextval('public.test_submissions_id_seq'::regclass);


--
-- TOC entry 3394 (class 2604 OID 122884)
-- Name: tests id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tests ALTER COLUMN id SET DEFAULT nextval('public.tests_id_seq'::regclass);


--
-- TOC entry 3393 (class 2604 OID 98368)
-- Name: tests_module id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tests_module ALTER COLUMN id SET DEFAULT nextval('public.tests_module_id_seq'::regclass);


--
-- TOC entry 3387 (class 2604 OID 41015)
-- Name: users id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- TOC entry 3771 (class 0 OID 139285)
-- Dependencies: 254
-- Data for Name: assignment_resources; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.assignment_resources (id, assignment_id, file_name, file_path, file_type, uploaded_at) FROM stdin;
4	14	sample.pdf	uploads/assignments/14/e3a3db4f44584bea9355fd7dff0fac10.pdf	application/pdf	2026-04-01 08:27:20.88277
9	30	Desktop - 6.pdf	uploads/assignments/30/badc92c68b4b4e1cb7d3880fe6c9d15d.pdf	application/pdf	2026-04-03 06:02:42.992996
10	30	Desktop - 10.pdf	uploads/assignments/30/b2ea6ebb9608456584850e2f2aaa36c8.pdf	application/pdf	2026-04-03 06:03:15.994228
11	31	Desktop - 7.pdf	uploads/assignments/31/2c2350d2b9e3415ebb32b4e343ec4824.pdf	application/pdf	2026-04-06 06:22:21.310115
12	34	Instagram post - 186.png	uploads/assignments/34/5442ac3fad1f4f6796a560c3e2e8a75c.png	image/png	2026-05-06 07:10:45.192963
\.


--
-- TOC entry 3773 (class 0 OID 139300)
-- Dependencies: 256
-- Data for Name: assignment_submissions; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.assignment_submissions (id, assignment_id, student_user_id, submission_text, file_path, file_name, submitted_at, status, grade, feedback) FROM stdin;
3	28	7	\N	\N	\N	2026-04-04 10:39:06.178933	graded	90	Very Good 
4	25	7	\N	\N	\N	2026-04-04 12:52:21.316256	submitted	\N	\N
2	30	7	\N	\N	\N	2026-04-06 06:18:46.979163	submitted	90	Good
6	24	7	\N	\N	\N	2026-04-06 10:33:44.894572	submitted	\N	\N
5	31	7	\N	\N	\N	2026-04-06 08:22:18.103084	graded	100	Good
1	14	7	hi mam i am completed the assigment 	\N	\N	2026-04-06 12:14:45.097916	submitted	80	good
7	32	7	\N	\N	\N	2026-04-06 12:20:49.872927	graded	96	Good Kuberan Your Assignment Is Really Good \n
8	33	7	\N	\N	\N	2026-04-06 12:41:56.714307	submitted	\N	\N
9	34	7	\N	\N	\N	2026-05-06 07:12:38.058409	graded	78	Good 
\.


--
-- TOC entry 3769 (class 0 OID 139265)
-- Dependencies: 252
-- Data for Name: assignments; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.assignments (id, course_id, batch_name, module_name, title, description, expected_outcome, due_date, created_by, created_at) FROM stdin;
14	1	Batch-A	Frontier Engineering Techniques	Design and manage assignment details efficiently.	Design and manage assignment details efficiently.\r\n\r\n	Design and manage assignment details efficiently.\r\n\r\n	2026-03-29 18:30:00	6	2026-04-01 08:27:19.356631
24	1	Batch-A	Frontier Engineering Techniques	Vishva 	Vadsddsd	Gfjnhgfjytudyf	2026-04-03 03:30:00	6	2026-04-02 06:07:48.4622
25	1	Batch-A	Frontier Engineering Techniques	Dfdfdfdfd	Dfdfdf	Fdffdfdfdf	2026-03-31 03:30:00	6	2026-04-02 06:09:20.311662
28	1	Batch-A	Frontier Engineering Techniques	Create Assignment 2	Xzxzs	Asas	2026-04-01 22:00:00	6	2026-04-02 07:58:44.702987
30	1	Batch-A	Introduction to AI & Machine Learning	Batch-B	Sdbfjkbfsdfsdfsdsf	Dfsdfdsfdf	2026-04-07 16:30:00	6	2026-04-03 06:02:39.481815
31	1	Batch-A	Frontier Engineering Techniques	Rahul	Sdfsafsdf	Sdfsdfsdf	2026-04-08 03:30:00	6	2026-04-06 06:22:17.932982
32	1	Batch-A	Frontier Engineering Techniques	Kuberan	Dsfsdf	Dadda	2026-04-15 03:30:00	6	2026-04-06 11:03:00.838562
33	1	Batch-A	Frontier Engineering Techniques	Siva Mani	Asasasa	Sasas	2026-04-11 03:30:00	6	2026-04-06 12:41:14.251744
34	1	Batch-A	Introduction to AI & Machine Learning	Sample 1	Eeddedc	Scskjjbnk	2026-05-06 18:30:00	6	2026-05-06 07:10:37.699553
\.


--
-- TOC entry 3755 (class 0 OID 98350)
-- Dependencies: 238
-- Data for Name: assignments_module; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.assignments_module (id, title, due_date, module_id) FROM stdin;
\.


--
-- TOC entry 3751 (class 0 OID 98320)
-- Dependencies: 234
-- Data for Name: chapters; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.chapters (id, title, "order", module_id) FROM stdin;
1	Foundations of AI	1	1
2	Python for ML	2	1
3	Advanced Prompt Engineering	1	2
4	string	1	1
\.


--
-- TOC entry 3781 (class 0 OID 147515)
-- Dependencies: 264
-- Data for Name: chat_bookmarks; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.chat_bookmarks (id, post_id, user_id, created_at) FROM stdin;
\.


--
-- TOC entry 3779 (class 0 OID 147497)
-- Dependencies: 262
-- Data for Name: chat_likes; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.chat_likes (id, post_id, user_id, created_at) FROM stdin;
\.


--
-- TOC entry 3775 (class 0 OID 147457)
-- Dependencies: 258
-- Data for Name: chat_posts; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.chat_posts (id, course_id, batch_name, author_id, author_role, content, created_at, updated_at, is_pinned, pinned_at) FROM stdin;
\.


--
-- TOC entry 3777 (class 0 OID 147477)
-- Dependencies: 260
-- Data for Name: chat_replies; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.chat_replies (id, post_id, author_id, author_role, content, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 3787 (class 0 OID 188417)
-- Dependencies: 270
-- Data for Name: chat_reply_likes; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.chat_reply_likes (id, reply_id, user_id, created_at) FROM stdin;
\.


--
-- TOC entry 3734 (class 0 OID 40972)
-- Dependencies: 217
-- Data for Name: class_sessions; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.class_sessions (id, classroom_id, start_time, end_time, status, join_url, course_id, batch_name, livekit_room_name, host_url, egress_id) FROM stdin;
1	1	2026-05-07 20:12:49.960943	\N	live	https://coirei-videoconf-1840.app.100ms.live/meeting/mhd-mnos-oso	1	Batch-A	69b6b10e247ff90ac99808f6	https://coirei-videoconf-1840.app.100ms.live/meeting/bwk-escj-zfv	\N
13	\N	2026-04-03 13:08:52.926398	2026-04-07 20:05:53.844555	ended	https://coirei-videoconf-1840.app.100ms.live/meeting/osz-rpvk-utp	1	Batch-B	69ce67a8eec71eb26f1f6fd4	https://coirei-videoconf-1840.app.100ms.live/meeting/rys-uiuh-jkd	\N
\.


--
-- TOC entry 3736 (class 0 OID 40978)
-- Dependencies: 219
-- Data for Name: classrooms; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.classrooms (id, course_name, batch_name, room_name, course_id) FROM stdin;
1	AI/ML frontier Engineer	Batch-A	AI_ML_Frontier_Room	1
\.


--
-- TOC entry 3747 (class 0 OID 90113)
-- Dependencies: 230
-- Data for Name: course_schedules; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.course_schedules (id, course_id, batch_name, day_of_week, session_type, start_time, end_time, instructor_name) FROM stdin;
\.


--
-- TOC entry 3738 (class 0 OID 40984)
-- Dependencies: 221
-- Data for Name: courses; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.courses (id, name, duration_months, total_lessons) FROM stdin;
1	AI/ML frontier Engineer	3	40
\.


--
-- TOC entry 3789 (class 0 OID 188435)
-- Dependencies: 272
-- Data for Name: dm_conversations; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.dm_conversations (id, user_a_id, user_b_id, unread_a, unread_b, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 3799 (class 0 OID 188532)
-- Dependencies: 282
-- Data for Name: dm_message_bookmarks; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.dm_message_bookmarks (id, message_id, user_id, created_at) FROM stdin;
\.


--
-- TOC entry 3797 (class 0 OID 188512)
-- Dependencies: 280
-- Data for Name: dm_message_likes; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.dm_message_likes (id, message_id, user_id, created_at) FROM stdin;
\.


--
-- TOC entry 3793 (class 0 OID 188472)
-- Dependencies: 276
-- Data for Name: dm_messages; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.dm_messages (id, conversation_id, sender_id, text, attachment_url, attachment_name, created_at, deleted_at) FROM stdin;
\.


--
-- TOC entry 3740 (class 0 OID 40990)
-- Dependencies: 223
-- Data for Name: enrollments; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.enrollments (id, user_id, course_id, progress_percent, status, classroom_id, batch_name) FROM stdin;
1	7	1	0	ongoing	\N	Batch-A
2	20	1	0	ongoing	\N	Batch-A
3	21	1	0	ongoing	\N	Batch-A
4	22	1	0	ongoing	\N	Batch-A
5	23	1	0	ongoing	\N	Batch-A
6	24	1	0	ongoing	\N	Batch-A
7	25	1	0	ongoing	\N	Batch-A
8	26	1	0	ongoing	\N	Batch-A
9	27	1	0	ongoing	\N	Batch-A
10	28	1	0	ongoing	\N	Batch-A
11	29	1	0	ongoing	\N	Batch-A
12	30	1	0	ongoing	\N	Batch-A
13	34	1	0	ongoing	\N	Batch-A
14	35	1	0	ongoing	\N	Batch-A
15	36	1	0	ongoing	\N	Batch-A
16	37	1	0	ongoing	\N	Batch-A
17	38	1	0	ongoing	\N	Batch-A
\.


--
-- TOC entry 3791 (class 0 OID 188455)
-- Dependencies: 274
-- Data for Name: group_chats; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.group_chats (id, course_id, batch_name, created_at) FROM stdin;
\.


--
-- TOC entry 3803 (class 0 OID 188572)
-- Dependencies: 286
-- Data for Name: group_message_bookmarks; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.group_message_bookmarks (id, message_id, user_id, created_at) FROM stdin;
\.


--
-- TOC entry 3801 (class 0 OID 188552)
-- Dependencies: 284
-- Data for Name: group_message_likes; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.group_message_likes (id, message_id, user_id, created_at) FROM stdin;
\.


--
-- TOC entry 3795 (class 0 OID 188492)
-- Dependencies: 278
-- Data for Name: group_messages; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.group_messages (id, group_id, sender_id, sender_role, text, attachment_url, attachment_name, is_pinned, pinned_at, created_at, deleted_at) FROM stdin;
\.


--
-- TOC entry 3785 (class 0 OID 180225)
-- Dependencies: 268
-- Data for Name: instructor_enrollments; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.instructor_enrollments (id, user_id, course_id, batch_name) FROM stdin;
\.


--
-- TOC entry 3749 (class 0 OID 98305)
-- Dependencies: 232
-- Data for Name: modules; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.modules (id, title, "order", status, course_id, batch_name) FROM stdin;
1	Introduction to AI & Machine Learning	1	Ongoing	1	Batch-A
2	Frontier Engineering Techniques	2	Ongoing	1	Batch-A
\.


--
-- TOC entry 3783 (class 0 OID 172033)
-- Dependencies: 266
-- Data for Name: notifications; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.notifications (id, user_id, type, title, message, is_read, created_at, related_id) FROM stdin;
2	20	assignment	New Assignment	newwewewe has been posted for Batch-A.	f	2026-03-30 10:29:57.243593	9
3	21	assignment	New Assignment	newwewewe has been posted for Batch-A.	f	2026-03-30 10:29:57.243594	9
4	22	assignment	New Assignment	newwewewe has been posted for Batch-A.	f	2026-03-30 10:29:57.243595	9
5	23	assignment	New Assignment	newwewewe has been posted for Batch-A.	f	2026-03-30 10:29:57.243595	9
6	24	assignment	New Assignment	newwewewe has been posted for Batch-A.	f	2026-03-30 10:29:57.243596	9
7	25	assignment	New Assignment	newwewewe has been posted for Batch-A.	f	2026-03-30 10:29:57.243596	9
8	26	assignment	New Assignment	newwewewe has been posted for Batch-A.	f	2026-03-30 10:29:57.243597	9
9	27	assignment	New Assignment	newwewewe has been posted for Batch-A.	f	2026-03-30 10:29:57.243597	9
10	28	assignment	New Assignment	newwewewe has been posted for Batch-A.	f	2026-03-30 10:29:57.243598	9
11	29	assignment	New Assignment	newwewewe has been posted for Batch-A.	f	2026-03-30 10:29:57.243598	9
12	30	assignment	New Assignment	newwewewe has been posted for Batch-A.	f	2026-03-30 10:29:57.243599	9
14	20	assignment	New Assignment	sample has been posted for Batch-A.	f	2026-03-30 10:32:35.118296	10
15	21	assignment	New Assignment	sample has been posted for Batch-A.	f	2026-03-30 10:32:35.118297	10
16	22	assignment	New Assignment	sample has been posted for Batch-A.	f	2026-03-30 10:32:35.118298	10
17	23	assignment	New Assignment	sample has been posted for Batch-A.	f	2026-03-30 10:32:35.118298	10
18	24	assignment	New Assignment	sample has been posted for Batch-A.	f	2026-03-30 10:32:35.118299	10
19	25	assignment	New Assignment	sample has been posted for Batch-A.	f	2026-03-30 10:32:35.1183	10
20	26	assignment	New Assignment	sample has been posted for Batch-A.	f	2026-03-30 10:32:35.1183	10
21	27	assignment	New Assignment	sample has been posted for Batch-A.	f	2026-03-30 10:32:35.118301	10
22	28	assignment	New Assignment	sample has been posted for Batch-A.	f	2026-03-30 10:32:35.118302	10
23	29	assignment	New Assignment	sample has been posted for Batch-A.	f	2026-03-30 10:32:35.118302	10
24	30	assignment	New Assignment	sample has been posted for Batch-A.	f	2026-03-30 10:32:35.118303	10
26	20	assignment	New Assignment	12345 has been posted for Batch-A.	f	2026-03-30 10:37:26.223065	11
27	21	assignment	New Assignment	12345 has been posted for Batch-A.	f	2026-03-30 10:37:26.223065	11
28	22	assignment	New Assignment	12345 has been posted for Batch-A.	f	2026-03-30 10:37:26.223066	11
29	23	assignment	New Assignment	12345 has been posted for Batch-A.	f	2026-03-30 10:37:26.223067	11
30	24	assignment	New Assignment	12345 has been posted for Batch-A.	f	2026-03-30 10:37:26.223068	11
31	25	assignment	New Assignment	12345 has been posted for Batch-A.	f	2026-03-30 10:37:26.223069	11
32	26	assignment	New Assignment	12345 has been posted for Batch-A.	f	2026-03-30 10:37:26.223069	11
33	27	assignment	New Assignment	12345 has been posted for Batch-A.	f	2026-03-30 10:37:26.22307	11
34	28	assignment	New Assignment	12345 has been posted for Batch-A.	f	2026-03-30 10:37:26.22307	11
35	29	assignment	New Assignment	12345 has been posted for Batch-A.	f	2026-03-30 10:37:26.223071	11
36	30	assignment	New Assignment	12345 has been posted for Batch-A.	f	2026-03-30 10:37:26.223071	11
1	7	assignment	New Assignment	newwewewe has been posted for Batch-A.	t	2026-03-30 10:29:57.243588	9
13	7	assignment	New Assignment	sample has been posted for Batch-A.	t	2026-03-30 10:32:35.118292	10
25	7	assignment	New Assignment	12345 has been posted for Batch-A.	t	2026-03-30 10:37:26.223061	11
37	7	assignment	New Assignment	Function and loop Assignment  has been posted for Batch-A.	f	2026-04-01 06:46:57.638449	12
38	20	assignment	New Assignment	Function and loop Assignment  has been posted for Batch-A.	f	2026-04-01 06:46:57.638453	12
39	21	assignment	New Assignment	Function and loop Assignment  has been posted for Batch-A.	f	2026-04-01 06:46:57.638454	12
40	22	assignment	New Assignment	Function and loop Assignment  has been posted for Batch-A.	f	2026-04-01 06:46:57.638455	12
41	23	assignment	New Assignment	Function and loop Assignment  has been posted for Batch-A.	f	2026-04-01 06:46:57.638455	12
42	24	assignment	New Assignment	Function and loop Assignment  has been posted for Batch-A.	f	2026-04-01 06:46:57.638456	12
43	25	assignment	New Assignment	Function and loop Assignment  has been posted for Batch-A.	f	2026-04-01 06:46:57.638456	12
44	26	assignment	New Assignment	Function and loop Assignment  has been posted for Batch-A.	f	2026-04-01 06:46:57.638457	12
45	27	assignment	New Assignment	Function and loop Assignment  has been posted for Batch-A.	f	2026-04-01 06:46:57.638457	12
46	28	assignment	New Assignment	Function and loop Assignment  has been posted for Batch-A.	f	2026-04-01 06:46:57.638457	12
47	29	assignment	New Assignment	Function and loop Assignment  has been posted for Batch-A.	f	2026-04-01 06:46:57.638458	12
48	30	assignment	New Assignment	Function and loop Assignment  has been posted for Batch-A.	f	2026-04-01 06:46:57.638458	12
49	7	assignment	New Assignment	New Test Assignment has been posted for Batch-A.	f	2026-04-01 08:14:15.773882	13
50	20	assignment	New Assignment	New Test Assignment has been posted for Batch-A.	f	2026-04-01 08:14:15.773887	13
51	21	assignment	New Assignment	New Test Assignment has been posted for Batch-A.	f	2026-04-01 08:14:15.773888	13
52	22	assignment	New Assignment	New Test Assignment has been posted for Batch-A.	f	2026-04-01 08:14:15.773888	13
53	23	assignment	New Assignment	New Test Assignment has been posted for Batch-A.	f	2026-04-01 08:14:15.773889	13
54	24	assignment	New Assignment	New Test Assignment has been posted for Batch-A.	f	2026-04-01 08:14:15.773889	13
55	25	assignment	New Assignment	New Test Assignment has been posted for Batch-A.	f	2026-04-01 08:14:15.77389	13
56	26	assignment	New Assignment	New Test Assignment has been posted for Batch-A.	f	2026-04-01 08:14:15.77389	13
57	27	assignment	New Assignment	New Test Assignment has been posted for Batch-A.	f	2026-04-01 08:14:15.77389	13
58	28	assignment	New Assignment	New Test Assignment has been posted for Batch-A.	f	2026-04-01 08:14:15.773891	13
59	29	assignment	New Assignment	New Test Assignment has been posted for Batch-A.	f	2026-04-01 08:14:15.773891	13
60	30	assignment	New Assignment	New Test Assignment has been posted for Batch-A.	f	2026-04-01 08:14:15.773892	13
61	7	assignment	New Assignment	Design and manage assignment details efficiently. has been posted for Batch-A.	f	2026-04-01 08:27:19.717432	14
62	20	assignment	New Assignment	Design and manage assignment details efficiently. has been posted for Batch-A.	f	2026-04-01 08:27:19.717435	14
63	21	assignment	New Assignment	Design and manage assignment details efficiently. has been posted for Batch-A.	f	2026-04-01 08:27:19.717436	14
64	22	assignment	New Assignment	Design and manage assignment details efficiently. has been posted for Batch-A.	f	2026-04-01 08:27:19.717436	14
65	23	assignment	New Assignment	Design and manage assignment details efficiently. has been posted for Batch-A.	f	2026-04-01 08:27:19.717436	14
66	24	assignment	New Assignment	Design and manage assignment details efficiently. has been posted for Batch-A.	f	2026-04-01 08:27:19.717437	14
67	25	assignment	New Assignment	Design and manage assignment details efficiently. has been posted for Batch-A.	f	2026-04-01 08:27:19.717437	14
68	26	assignment	New Assignment	Design and manage assignment details efficiently. has been posted for Batch-A.	f	2026-04-01 08:27:19.717438	14
69	27	assignment	New Assignment	Design and manage assignment details efficiently. has been posted for Batch-A.	f	2026-04-01 08:27:19.717438	14
70	28	assignment	New Assignment	Design and manage assignment details efficiently. has been posted for Batch-A.	f	2026-04-01 08:27:19.717438	14
71	29	assignment	New Assignment	Design and manage assignment details efficiently. has been posted for Batch-A.	f	2026-04-01 08:27:19.717439	14
72	30	assignment	New Assignment	Design and manage assignment details efficiently. has been posted for Batch-A.	f	2026-04-01 08:27:19.717439	14
73	7	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 08:58:45.587601	15
74	20	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 08:58:45.587604	15
75	21	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 08:58:45.587605	15
76	22	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 08:58:45.587605	15
77	23	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 08:58:45.587606	15
78	24	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 08:58:45.587606	15
79	25	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 08:58:45.587607	15
80	26	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 08:58:45.587607	15
81	27	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 08:58:45.587608	15
82	28	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 08:58:45.587608	15
83	29	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 08:58:45.587609	15
84	30	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 08:58:45.587609	15
85	7	assignment	New Assignment	ass has been posted for Batch-A.	f	2026-04-01 10:08:48.062892	16
86	20	assignment	New Assignment	ass has been posted for Batch-A.	f	2026-04-01 10:08:48.062896	16
87	21	assignment	New Assignment	ass has been posted for Batch-A.	f	2026-04-01 10:08:48.062896	16
88	22	assignment	New Assignment	ass has been posted for Batch-A.	f	2026-04-01 10:08:48.062897	16
89	23	assignment	New Assignment	ass has been posted for Batch-A.	f	2026-04-01 10:08:48.062897	16
90	24	assignment	New Assignment	ass has been posted for Batch-A.	f	2026-04-01 10:08:48.062898	16
91	25	assignment	New Assignment	ass has been posted for Batch-A.	f	2026-04-01 10:08:48.062898	16
92	26	assignment	New Assignment	ass has been posted for Batch-A.	f	2026-04-01 10:08:48.062899	16
93	27	assignment	New Assignment	ass has been posted for Batch-A.	f	2026-04-01 10:08:48.062899	16
94	28	assignment	New Assignment	ass has been posted for Batch-A.	f	2026-04-01 10:08:48.0629	16
95	29	assignment	New Assignment	ass has been posted for Batch-A.	f	2026-04-01 10:08:48.062901	16
96	30	assignment	New Assignment	ass has been posted for Batch-A.	f	2026-04-01 10:08:48.062901	16
97	7	assignment	New Assignment	sssssssssssss has been posted for Batch-A.	f	2026-04-01 10:14:56.343009	17
98	20	assignment	New Assignment	sssssssssssss has been posted for Batch-A.	f	2026-04-01 10:14:56.343013	17
99	21	assignment	New Assignment	sssssssssssss has been posted for Batch-A.	f	2026-04-01 10:14:56.343014	17
100	22	assignment	New Assignment	sssssssssssss has been posted for Batch-A.	f	2026-04-01 10:14:56.343015	17
101	23	assignment	New Assignment	sssssssssssss has been posted for Batch-A.	f	2026-04-01 10:14:56.343016	17
102	24	assignment	New Assignment	sssssssssssss has been posted for Batch-A.	f	2026-04-01 10:14:56.343016	17
103	25	assignment	New Assignment	sssssssssssss has been posted for Batch-A.	f	2026-04-01 10:14:56.343017	17
104	26	assignment	New Assignment	sssssssssssss has been posted for Batch-A.	f	2026-04-01 10:14:56.343017	17
105	27	assignment	New Assignment	sssssssssssss has been posted for Batch-A.	f	2026-04-01 10:14:56.343018	17
106	28	assignment	New Assignment	sssssssssssss has been posted for Batch-A.	f	2026-04-01 10:14:56.343019	17
107	29	assignment	New Assignment	sssssssssssss has been posted for Batch-A.	f	2026-04-01 10:14:56.343019	17
108	30	assignment	New Assignment	sssssssssssss has been posted for Batch-A.	f	2026-04-01 10:14:56.34302	17
109	7	assignment	New Assignment	asasa has been posted for Batch-A.	f	2026-04-01 10:23:32.104527	18
110	20	assignment	New Assignment	asasa has been posted for Batch-A.	f	2026-04-01 10:23:32.104532	18
111	21	assignment	New Assignment	asasa has been posted for Batch-A.	f	2026-04-01 10:23:32.104533	18
112	22	assignment	New Assignment	asasa has been posted for Batch-A.	f	2026-04-01 10:23:32.104534	18
113	23	assignment	New Assignment	asasa has been posted for Batch-A.	f	2026-04-01 10:23:32.104535	18
114	24	assignment	New Assignment	asasa has been posted for Batch-A.	f	2026-04-01 10:23:32.104535	18
115	25	assignment	New Assignment	asasa has been posted for Batch-A.	f	2026-04-01 10:23:32.104536	18
116	26	assignment	New Assignment	asasa has been posted for Batch-A.	f	2026-04-01 10:23:32.104537	18
117	27	assignment	New Assignment	asasa has been posted for Batch-A.	f	2026-04-01 10:23:32.104537	18
118	28	assignment	New Assignment	asasa has been posted for Batch-A.	f	2026-04-01 10:23:32.104538	18
119	29	assignment	New Assignment	asasa has been posted for Batch-A.	f	2026-04-01 10:23:32.104539	18
120	30	assignment	New Assignment	asasa has been posted for Batch-A.	f	2026-04-01 10:23:32.10454	18
121	7	assignment	New Assignment	sssssssssssssssssssss has been posted for Batch-A.	f	2026-04-01 11:44:52.010813	19
122	20	assignment	New Assignment	sssssssssssssssssssss has been posted for Batch-A.	f	2026-04-01 11:44:52.01082	19
123	21	assignment	New Assignment	sssssssssssssssssssss has been posted for Batch-A.	f	2026-04-01 11:44:52.010821	19
124	22	assignment	New Assignment	sssssssssssssssssssss has been posted for Batch-A.	f	2026-04-01 11:44:52.010822	19
125	23	assignment	New Assignment	sssssssssssssssssssss has been posted for Batch-A.	f	2026-04-01 11:44:52.010822	19
126	24	assignment	New Assignment	sssssssssssssssssssss has been posted for Batch-A.	f	2026-04-01 11:44:52.010823	19
127	25	assignment	New Assignment	sssssssssssssssssssss has been posted for Batch-A.	f	2026-04-01 11:44:52.010823	19
128	26	assignment	New Assignment	sssssssssssssssssssss has been posted for Batch-A.	f	2026-04-01 11:44:52.010824	19
129	27	assignment	New Assignment	sssssssssssssssssssss has been posted for Batch-A.	f	2026-04-01 11:44:52.010825	19
130	28	assignment	New Assignment	sssssssssssssssssssss has been posted for Batch-A.	f	2026-04-01 11:44:52.010825	19
131	29	assignment	New Assignment	sssssssssssssssssssss has been posted for Batch-A.	f	2026-04-01 11:44:52.010826	19
132	30	assignment	New Assignment	sssssssssssssssssssss has been posted for Batch-A.	f	2026-04-01 11:44:52.010826	19
133	7	assignment	New Assignment	vishva has been posted for Batch-A.	f	2026-04-01 11:45:41.078335	20
134	20	assignment	New Assignment	vishva has been posted for Batch-A.	f	2026-04-01 11:45:41.078339	20
135	21	assignment	New Assignment	vishva has been posted for Batch-A.	f	2026-04-01 11:45:41.078339	20
136	22	assignment	New Assignment	vishva has been posted for Batch-A.	f	2026-04-01 11:45:41.078339	20
137	23	assignment	New Assignment	vishva has been posted for Batch-A.	f	2026-04-01 11:45:41.07834	20
138	24	assignment	New Assignment	vishva has been posted for Batch-A.	f	2026-04-01 11:45:41.07834	20
139	25	assignment	New Assignment	vishva has been posted for Batch-A.	f	2026-04-01 11:45:41.078341	20
140	26	assignment	New Assignment	vishva has been posted for Batch-A.	f	2026-04-01 11:45:41.078341	20
141	27	assignment	New Assignment	vishva has been posted for Batch-A.	f	2026-04-01 11:45:41.078341	20
142	28	assignment	New Assignment	vishva has been posted for Batch-A.	f	2026-04-01 11:45:41.078342	20
143	29	assignment	New Assignment	vishva has been posted for Batch-A.	f	2026-04-01 11:45:41.078342	20
144	30	assignment	New Assignment	vishva has been posted for Batch-A.	f	2026-04-01 11:45:41.078343	20
145	7	assignment	New Assignment	sas has been posted for Batch-A.	f	2026-04-01 11:49:03.352827	21
146	20	assignment	New Assignment	sas has been posted for Batch-A.	f	2026-04-01 11:49:03.352832	21
147	21	assignment	New Assignment	sas has been posted for Batch-A.	f	2026-04-01 11:49:03.352832	21
148	22	assignment	New Assignment	sas has been posted for Batch-A.	f	2026-04-01 11:49:03.352833	21
149	23	assignment	New Assignment	sas has been posted for Batch-A.	f	2026-04-01 11:49:03.352833	21
150	24	assignment	New Assignment	sas has been posted for Batch-A.	f	2026-04-01 11:49:03.352834	21
151	25	assignment	New Assignment	sas has been posted for Batch-A.	f	2026-04-01 11:49:03.352834	21
152	26	assignment	New Assignment	sas has been posted for Batch-A.	f	2026-04-01 11:49:03.352835	21
153	27	assignment	New Assignment	sas has been posted for Batch-A.	f	2026-04-01 11:49:03.352835	21
154	28	assignment	New Assignment	sas has been posted for Batch-A.	f	2026-04-01 11:49:03.352836	21
155	29	assignment	New Assignment	sas has been posted for Batch-A.	f	2026-04-01 11:49:03.352837	21
156	30	assignment	New Assignment	sas has been posted for Batch-A.	f	2026-04-01 11:49:03.352837	21
157	7	assignment	New Assignment	Asas Sasas Asasasa has been posted for Batch-A.	f	2026-04-01 11:58:42.671222	22
158	20	assignment	New Assignment	Asas Sasas Asasasa has been posted for Batch-A.	f	2026-04-01 11:58:42.671225	22
159	21	assignment	New Assignment	Asas Sasas Asasasa has been posted for Batch-A.	f	2026-04-01 11:58:42.671226	22
160	22	assignment	New Assignment	Asas Sasas Asasasa has been posted for Batch-A.	f	2026-04-01 11:58:42.671226	22
161	23	assignment	New Assignment	Asas Sasas Asasasa has been posted for Batch-A.	f	2026-04-01 11:58:42.671226	22
162	24	assignment	New Assignment	Asas Sasas Asasasa has been posted for Batch-A.	f	2026-04-01 11:58:42.671227	22
163	25	assignment	New Assignment	Asas Sasas Asasasa has been posted for Batch-A.	f	2026-04-01 11:58:42.671227	22
164	26	assignment	New Assignment	Asas Sasas Asasasa has been posted for Batch-A.	f	2026-04-01 11:58:42.671227	22
165	27	assignment	New Assignment	Asas Sasas Asasasa has been posted for Batch-A.	f	2026-04-01 11:58:42.671228	22
166	28	assignment	New Assignment	Asas Sasas Asasasa has been posted for Batch-A.	f	2026-04-01 11:58:42.671228	22
167	29	assignment	New Assignment	Asas Sasas Asasasa has been posted for Batch-A.	f	2026-04-01 11:58:42.671228	22
168	30	assignment	New Assignment	Asas Sasas Asasasa has been posted for Batch-A.	f	2026-04-01 11:58:42.671229	22
169	7	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 12:13:18.410788	23
170	20	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 12:13:18.410792	23
171	21	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 12:13:18.410792	23
172	22	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 12:13:18.410792	23
173	23	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 12:13:18.410793	23
174	24	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 12:13:18.410793	23
175	25	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 12:13:18.410794	23
176	26	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 12:13:18.410794	23
177	27	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 12:13:18.410794	23
178	28	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 12:13:18.410795	23
179	29	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 12:13:18.410795	23
180	30	assignment	New Assignment	Asasasasa has been posted for Batch-A.	f	2026-04-01 12:13:18.410796	23
181	7	assignment	New Assignment	Vishva  has been posted for Batch-A.	f	2026-04-02 06:07:48.824141	24
182	20	assignment	New Assignment	Vishva  has been posted for Batch-A.	f	2026-04-02 06:07:48.824146	24
183	21	assignment	New Assignment	Vishva  has been posted for Batch-A.	f	2026-04-02 06:07:48.824147	24
184	22	assignment	New Assignment	Vishva  has been posted for Batch-A.	f	2026-04-02 06:07:48.824148	24
185	23	assignment	New Assignment	Vishva  has been posted for Batch-A.	f	2026-04-02 06:07:48.824149	24
186	24	assignment	New Assignment	Vishva  has been posted for Batch-A.	f	2026-04-02 06:07:48.824149	24
187	25	assignment	New Assignment	Vishva  has been posted for Batch-A.	f	2026-04-02 06:07:48.82415	24
188	26	assignment	New Assignment	Vishva  has been posted for Batch-A.	f	2026-04-02 06:07:48.824151	24
189	27	assignment	New Assignment	Vishva  has been posted for Batch-A.	f	2026-04-02 06:07:48.824152	24
190	28	assignment	New Assignment	Vishva  has been posted for Batch-A.	f	2026-04-02 06:07:48.824152	24
191	29	assignment	New Assignment	Vishva  has been posted for Batch-A.	f	2026-04-02 06:07:48.824153	24
192	30	assignment	New Assignment	Vishva  has been posted for Batch-A.	f	2026-04-02 06:07:48.824153	24
193	34	assignment	New Assignment	Vishva  has been posted for Batch-A.	f	2026-04-02 06:07:48.824154	24
194	35	assignment	New Assignment	Vishva  has been posted for Batch-A.	f	2026-04-02 06:07:48.824155	24
195	36	assignment	New Assignment	Vishva  has been posted for Batch-A.	f	2026-04-02 06:07:48.824155	24
196	37	assignment	New Assignment	Vishva  has been posted for Batch-A.	f	2026-04-02 06:07:48.824156	24
197	7	assignment	New Assignment	Dfdfdfdfd has been posted for Batch-A.	f	2026-04-02 06:09:20.715874	25
198	20	assignment	New Assignment	Dfdfdfdfd has been posted for Batch-A.	f	2026-04-02 06:09:20.715877	25
199	21	assignment	New Assignment	Dfdfdfdfd has been posted for Batch-A.	f	2026-04-02 06:09:20.715878	25
200	22	assignment	New Assignment	Dfdfdfdfd has been posted for Batch-A.	f	2026-04-02 06:09:20.715878	25
201	23	assignment	New Assignment	Dfdfdfdfd has been posted for Batch-A.	f	2026-04-02 06:09:20.715878	25
202	24	assignment	New Assignment	Dfdfdfdfd has been posted for Batch-A.	f	2026-04-02 06:09:20.715879	25
203	25	assignment	New Assignment	Dfdfdfdfd has been posted for Batch-A.	f	2026-04-02 06:09:20.715879	25
204	26	assignment	New Assignment	Dfdfdfdfd has been posted for Batch-A.	f	2026-04-02 06:09:20.71588	25
205	27	assignment	New Assignment	Dfdfdfdfd has been posted for Batch-A.	f	2026-04-02 06:09:20.71588	25
206	28	assignment	New Assignment	Dfdfdfdfd has been posted for Batch-A.	f	2026-04-02 06:09:20.71588	25
207	29	assignment	New Assignment	Dfdfdfdfd has been posted for Batch-A.	f	2026-04-02 06:09:20.715881	25
208	30	assignment	New Assignment	Dfdfdfdfd has been posted for Batch-A.	f	2026-04-02 06:09:20.715881	25
209	34	assignment	New Assignment	Dfdfdfdfd has been posted for Batch-A.	f	2026-04-02 06:09:20.715881	25
210	35	assignment	New Assignment	Dfdfdfdfd has been posted for Batch-A.	f	2026-04-02 06:09:20.715882	25
211	36	assignment	New Assignment	Dfdfdfdfd has been posted for Batch-A.	f	2026-04-02 06:09:20.715882	25
212	37	assignment	New Assignment	Dfdfdfdfd has been posted for Batch-A.	f	2026-04-02 06:09:20.715883	25
213	7	assignment	New Assignment	Sdsdsd has been posted for Batch-A.	f	2026-04-02 07:15:51.648275	26
214	20	assignment	New Assignment	Sdsdsd has been posted for Batch-A.	f	2026-04-02 07:15:51.648281	26
215	21	assignment	New Assignment	Sdsdsd has been posted for Batch-A.	f	2026-04-02 07:15:51.648282	26
216	22	assignment	New Assignment	Sdsdsd has been posted for Batch-A.	f	2026-04-02 07:15:51.648283	26
217	23	assignment	New Assignment	Sdsdsd has been posted for Batch-A.	f	2026-04-02 07:15:51.648283	26
218	24	assignment	New Assignment	Sdsdsd has been posted for Batch-A.	f	2026-04-02 07:15:51.648284	26
219	25	assignment	New Assignment	Sdsdsd has been posted for Batch-A.	f	2026-04-02 07:15:51.648285	26
220	26	assignment	New Assignment	Sdsdsd has been posted for Batch-A.	f	2026-04-02 07:15:51.648285	26
221	27	assignment	New Assignment	Sdsdsd has been posted for Batch-A.	f	2026-04-02 07:15:51.648286	26
222	28	assignment	New Assignment	Sdsdsd has been posted for Batch-A.	f	2026-04-02 07:15:51.648286	26
223	29	assignment	New Assignment	Sdsdsd has been posted for Batch-A.	f	2026-04-02 07:15:51.648287	26
224	30	assignment	New Assignment	Sdsdsd has been posted for Batch-A.	f	2026-04-02 07:15:51.648288	26
225	34	assignment	New Assignment	Sdsdsd has been posted for Batch-A.	f	2026-04-02 07:15:51.648288	26
226	35	assignment	New Assignment	Sdsdsd has been posted for Batch-A.	f	2026-04-02 07:15:51.648289	26
227	36	assignment	New Assignment	Sdsdsd has been posted for Batch-A.	f	2026-04-02 07:15:51.648289	26
228	37	assignment	New Assignment	Sdsdsd has been posted for Batch-A.	f	2026-04-02 07:15:51.648291	26
229	7	assignment	New Assignment	Sdsdsdsdsdsd has been posted for Batch-A.	f	2026-04-02 07:16:39.368989	27
230	20	assignment	New Assignment	Sdsdsdsdsdsd has been posted for Batch-A.	f	2026-04-02 07:16:39.368992	27
231	21	assignment	New Assignment	Sdsdsdsdsdsd has been posted for Batch-A.	f	2026-04-02 07:16:39.368993	27
232	22	assignment	New Assignment	Sdsdsdsdsdsd has been posted for Batch-A.	f	2026-04-02 07:16:39.368994	27
233	23	assignment	New Assignment	Sdsdsdsdsdsd has been posted for Batch-A.	f	2026-04-02 07:16:39.368994	27
234	24	assignment	New Assignment	Sdsdsdsdsdsd has been posted for Batch-A.	f	2026-04-02 07:16:39.368994	27
235	25	assignment	New Assignment	Sdsdsdsdsdsd has been posted for Batch-A.	f	2026-04-02 07:16:39.368995	27
236	26	assignment	New Assignment	Sdsdsdsdsdsd has been posted for Batch-A.	f	2026-04-02 07:16:39.368995	27
237	27	assignment	New Assignment	Sdsdsdsdsdsd has been posted for Batch-A.	f	2026-04-02 07:16:39.368996	27
238	28	assignment	New Assignment	Sdsdsdsdsdsd has been posted for Batch-A.	f	2026-04-02 07:16:39.368996	27
239	29	assignment	New Assignment	Sdsdsdsdsdsd has been posted for Batch-A.	f	2026-04-02 07:16:39.368996	27
240	30	assignment	New Assignment	Sdsdsdsdsdsd has been posted for Batch-A.	f	2026-04-02 07:16:39.368997	27
241	34	assignment	New Assignment	Sdsdsdsdsdsd has been posted for Batch-A.	f	2026-04-02 07:16:39.368997	27
242	35	assignment	New Assignment	Sdsdsdsdsdsd has been posted for Batch-A.	f	2026-04-02 07:16:39.368998	27
243	36	assignment	New Assignment	Sdsdsdsdsdsd has been posted for Batch-A.	f	2026-04-02 07:16:39.368998	27
244	37	assignment	New Assignment	Sdsdsdsdsdsd has been posted for Batch-A.	f	2026-04-02 07:16:39.368998	27
245	7	assignment	New Assignment	Asdfghj has been posted for Batch-A.	f	2026-04-02 07:58:45.083483	28
246	20	assignment	New Assignment	Asdfghj has been posted for Batch-A.	f	2026-04-02 07:58:45.083485	28
247	21	assignment	New Assignment	Asdfghj has been posted for Batch-A.	f	2026-04-02 07:58:45.083486	28
248	22	assignment	New Assignment	Asdfghj has been posted for Batch-A.	f	2026-04-02 07:58:45.083486	28
249	23	assignment	New Assignment	Asdfghj has been posted for Batch-A.	f	2026-04-02 07:58:45.083487	28
250	24	assignment	New Assignment	Asdfghj has been posted for Batch-A.	f	2026-04-02 07:58:45.083487	28
251	25	assignment	New Assignment	Asdfghj has been posted for Batch-A.	f	2026-04-02 07:58:45.083488	28
252	26	assignment	New Assignment	Asdfghj has been posted for Batch-A.	f	2026-04-02 07:58:45.083488	28
253	27	assignment	New Assignment	Asdfghj has been posted for Batch-A.	f	2026-04-02 07:58:45.083488	28
254	28	assignment	New Assignment	Asdfghj has been posted for Batch-A.	f	2026-04-02 07:58:45.083489	28
255	29	assignment	New Assignment	Asdfghj has been posted for Batch-A.	f	2026-04-02 07:58:45.083489	28
256	30	assignment	New Assignment	Asdfghj has been posted for Batch-A.	f	2026-04-02 07:58:45.083489	28
257	34	assignment	New Assignment	Asdfghj has been posted for Batch-A.	f	2026-04-02 07:58:45.08349	28
258	35	assignment	New Assignment	Asdfghj has been posted for Batch-A.	f	2026-04-02 07:58:45.08349	28
259	36	assignment	New Assignment	Asdfghj has been posted for Batch-A.	f	2026-04-02 07:58:45.08349	28
260	37	assignment	New Assignment	Asdfghj has been posted for Batch-A.	f	2026-04-02 07:58:45.083491	28
261	7	assignment	New Assignment	Sample has been posted for Batch-A.	f	2026-04-02 09:19:15.378947	29
262	20	assignment	New Assignment	Sample has been posted for Batch-A.	f	2026-04-02 09:19:15.378953	29
263	21	assignment	New Assignment	Sample has been posted for Batch-A.	f	2026-04-02 09:19:15.378954	29
264	22	assignment	New Assignment	Sample has been posted for Batch-A.	f	2026-04-02 09:19:15.378955	29
265	23	assignment	New Assignment	Sample has been posted for Batch-A.	f	2026-04-02 09:19:15.378955	29
266	24	assignment	New Assignment	Sample has been posted for Batch-A.	f	2026-04-02 09:19:15.378956	29
267	25	assignment	New Assignment	Sample has been posted for Batch-A.	f	2026-04-02 09:19:15.378957	29
268	26	assignment	New Assignment	Sample has been posted for Batch-A.	f	2026-04-02 09:19:15.378957	29
269	27	assignment	New Assignment	Sample has been posted for Batch-A.	f	2026-04-02 09:19:15.378958	29
270	28	assignment	New Assignment	Sample has been posted for Batch-A.	f	2026-04-02 09:19:15.378958	29
271	29	assignment	New Assignment	Sample has been posted for Batch-A.	f	2026-04-02 09:19:15.378959	29
272	30	assignment	New Assignment	Sample has been posted for Batch-A.	f	2026-04-02 09:19:15.37896	29
273	34	assignment	New Assignment	Sample has been posted for Batch-A.	f	2026-04-02 09:19:15.37896	29
274	35	assignment	New Assignment	Sample has been posted for Batch-A.	f	2026-04-02 09:19:15.378961	29
275	36	assignment	New Assignment	Sample has been posted for Batch-A.	f	2026-04-02 09:19:15.378961	29
276	37	assignment	New Assignment	Sample has been posted for Batch-A.	f	2026-04-02 09:19:15.378962	29
277	7	assignment	New Assignment	Batch-B has been posted for Batch-A.	f	2026-04-03 06:02:39.851887	30
278	20	assignment	New Assignment	Batch-B has been posted for Batch-A.	f	2026-04-03 06:02:39.851892	30
279	21	assignment	New Assignment	Batch-B has been posted for Batch-A.	f	2026-04-03 06:02:39.851893	30
280	22	assignment	New Assignment	Batch-B has been posted for Batch-A.	f	2026-04-03 06:02:39.851894	30
281	23	assignment	New Assignment	Batch-B has been posted for Batch-A.	f	2026-04-03 06:02:39.851895	30
282	24	assignment	New Assignment	Batch-B has been posted for Batch-A.	f	2026-04-03 06:02:39.851896	30
283	25	assignment	New Assignment	Batch-B has been posted for Batch-A.	f	2026-04-03 06:02:39.851896	30
284	26	assignment	New Assignment	Batch-B has been posted for Batch-A.	f	2026-04-03 06:02:39.851897	30
285	27	assignment	New Assignment	Batch-B has been posted for Batch-A.	f	2026-04-03 06:02:39.851898	30
286	28	assignment	New Assignment	Batch-B has been posted for Batch-A.	f	2026-04-03 06:02:39.851898	30
287	29	assignment	New Assignment	Batch-B has been posted for Batch-A.	f	2026-04-03 06:02:39.851899	30
288	30	assignment	New Assignment	Batch-B has been posted for Batch-A.	f	2026-04-03 06:02:39.8519	30
289	34	assignment	New Assignment	Batch-B has been posted for Batch-A.	f	2026-04-03 06:02:39.8519	30
290	35	assignment	New Assignment	Batch-B has been posted for Batch-A.	f	2026-04-03 06:02:39.851901	30
291	36	assignment	New Assignment	Batch-B has been posted for Batch-A.	f	2026-04-03 06:02:39.851901	30
292	37	assignment	New Assignment	Batch-B has been posted for Batch-A.	f	2026-04-03 06:02:39.851902	30
293	7	assignment	New Assignment	Rahul has been posted for Batch-A.	f	2026-04-06 06:22:18.307199	31
294	20	assignment	New Assignment	Rahul has been posted for Batch-A.	f	2026-04-06 06:22:18.307205	31
295	21	assignment	New Assignment	Rahul has been posted for Batch-A.	f	2026-04-06 06:22:18.307206	31
296	22	assignment	New Assignment	Rahul has been posted for Batch-A.	f	2026-04-06 06:22:18.307206	31
297	23	assignment	New Assignment	Rahul has been posted for Batch-A.	f	2026-04-06 06:22:18.307207	31
298	24	assignment	New Assignment	Rahul has been posted for Batch-A.	f	2026-04-06 06:22:18.307207	31
299	25	assignment	New Assignment	Rahul has been posted for Batch-A.	f	2026-04-06 06:22:18.307208	31
300	26	assignment	New Assignment	Rahul has been posted for Batch-A.	f	2026-04-06 06:22:18.307209	31
301	27	assignment	New Assignment	Rahul has been posted for Batch-A.	f	2026-04-06 06:22:18.307209	31
302	28	assignment	New Assignment	Rahul has been posted for Batch-A.	f	2026-04-06 06:22:18.30721	31
303	29	assignment	New Assignment	Rahul has been posted for Batch-A.	f	2026-04-06 06:22:18.30721	31
304	30	assignment	New Assignment	Rahul has been posted for Batch-A.	f	2026-04-06 06:22:18.307211	31
305	34	assignment	New Assignment	Rahul has been posted for Batch-A.	f	2026-04-06 06:22:18.307211	31
306	35	assignment	New Assignment	Rahul has been posted for Batch-A.	f	2026-04-06 06:22:18.307211	31
307	36	assignment	New Assignment	Rahul has been posted for Batch-A.	f	2026-04-06 06:22:18.307212	31
308	37	assignment	New Assignment	Rahul has been posted for Batch-A.	f	2026-04-06 06:22:18.307212	31
309	7	assignment	New Assignment	Kuberan has been posted for Batch-A.	f	2026-04-06 11:03:01.330731	32
310	20	assignment	New Assignment	Kuberan has been posted for Batch-A.	f	2026-04-06 11:03:01.330737	32
311	21	assignment	New Assignment	Kuberan has been posted for Batch-A.	f	2026-04-06 11:03:01.330738	32
312	22	assignment	New Assignment	Kuberan has been posted for Batch-A.	f	2026-04-06 11:03:01.330739	32
313	23	assignment	New Assignment	Kuberan has been posted for Batch-A.	f	2026-04-06 11:03:01.33074	32
314	24	assignment	New Assignment	Kuberan has been posted for Batch-A.	f	2026-04-06 11:03:01.33074	32
315	25	assignment	New Assignment	Kuberan has been posted for Batch-A.	f	2026-04-06 11:03:01.330741	32
316	26	assignment	New Assignment	Kuberan has been posted for Batch-A.	f	2026-04-06 11:03:01.330742	32
317	27	assignment	New Assignment	Kuberan has been posted for Batch-A.	f	2026-04-06 11:03:01.330742	32
318	28	assignment	New Assignment	Kuberan has been posted for Batch-A.	f	2026-04-06 11:03:01.330743	32
319	29	assignment	New Assignment	Kuberan has been posted for Batch-A.	f	2026-04-06 11:03:01.330744	32
320	30	assignment	New Assignment	Kuberan has been posted for Batch-A.	f	2026-04-06 11:03:01.330744	32
321	34	assignment	New Assignment	Kuberan has been posted for Batch-A.	f	2026-04-06 11:03:01.330745	32
322	35	assignment	New Assignment	Kuberan has been posted for Batch-A.	f	2026-04-06 11:03:01.330745	32
323	36	assignment	New Assignment	Kuberan has been posted for Batch-A.	f	2026-04-06 11:03:01.330746	32
324	37	assignment	New Assignment	Kuberan has been posted for Batch-A.	f	2026-04-06 11:03:01.330747	32
325	7	assignment	New Assignment	Siva Mani has been posted for Batch-A.	f	2026-04-06 12:41:14.937692	33
326	20	assignment	New Assignment	Siva Mani has been posted for Batch-A.	f	2026-04-06 12:41:14.937696	33
327	21	assignment	New Assignment	Siva Mani has been posted for Batch-A.	f	2026-04-06 12:41:14.937697	33
328	22	assignment	New Assignment	Siva Mani has been posted for Batch-A.	f	2026-04-06 12:41:14.937697	33
329	23	assignment	New Assignment	Siva Mani has been posted for Batch-A.	f	2026-04-06 12:41:14.937698	33
330	24	assignment	New Assignment	Siva Mani has been posted for Batch-A.	f	2026-04-06 12:41:14.937698	33
331	25	assignment	New Assignment	Siva Mani has been posted for Batch-A.	f	2026-04-06 12:41:14.937698	33
332	26	assignment	New Assignment	Siva Mani has been posted for Batch-A.	f	2026-04-06 12:41:14.937699	33
333	27	assignment	New Assignment	Siva Mani has been posted for Batch-A.	f	2026-04-06 12:41:14.937699	33
334	28	assignment	New Assignment	Siva Mani has been posted for Batch-A.	f	2026-04-06 12:41:14.9377	33
335	29	assignment	New Assignment	Siva Mani has been posted for Batch-A.	f	2026-04-06 12:41:14.9377	33
336	30	assignment	New Assignment	Siva Mani has been posted for Batch-A.	f	2026-04-06 12:41:14.9377	33
337	34	assignment	New Assignment	Siva Mani has been posted for Batch-A.	f	2026-04-06 12:41:14.937701	33
338	35	assignment	New Assignment	Siva Mani has been posted for Batch-A.	f	2026-04-06 12:41:14.937702	33
339	36	assignment	New Assignment	Siva Mani has been posted for Batch-A.	f	2026-04-06 12:41:14.937702	33
340	37	assignment	New Assignment	Siva Mani has been posted for Batch-A.	f	2026-04-06 12:41:14.937703	33
341	7	assignment	New Assignment	Sample 1 has been posted for Batch-A.	f	2026-05-06 07:10:38.11383	34
342	20	assignment	New Assignment	Sample 1 has been posted for Batch-A.	f	2026-05-06 07:10:38.113836	34
343	21	assignment	New Assignment	Sample 1 has been posted for Batch-A.	f	2026-05-06 07:10:38.113837	34
344	22	assignment	New Assignment	Sample 1 has been posted for Batch-A.	f	2026-05-06 07:10:38.113837	34
345	23	assignment	New Assignment	Sample 1 has been posted for Batch-A.	f	2026-05-06 07:10:38.113838	34
346	24	assignment	New Assignment	Sample 1 has been posted for Batch-A.	f	2026-05-06 07:10:38.113838	34
347	25	assignment	New Assignment	Sample 1 has been posted for Batch-A.	f	2026-05-06 07:10:38.113839	34
348	26	assignment	New Assignment	Sample 1 has been posted for Batch-A.	f	2026-05-06 07:10:38.11384	34
349	27	assignment	New Assignment	Sample 1 has been posted for Batch-A.	f	2026-05-06 07:10:38.113841	34
350	28	assignment	New Assignment	Sample 1 has been posted for Batch-A.	f	2026-05-06 07:10:38.113841	34
351	29	assignment	New Assignment	Sample 1 has been posted for Batch-A.	f	2026-05-06 07:10:38.113842	34
352	30	assignment	New Assignment	Sample 1 has been posted for Batch-A.	f	2026-05-06 07:10:38.113843	34
353	34	assignment	New Assignment	Sample 1 has been posted for Batch-A.	f	2026-05-06 07:10:38.113843	34
354	35	assignment	New Assignment	Sample 1 has been posted for Batch-A.	f	2026-05-06 07:10:38.113844	34
355	36	assignment	New Assignment	Sample 1 has been posted for Batch-A.	f	2026-05-06 07:10:38.113845	34
356	37	assignment	New Assignment	Sample 1 has been posted for Batch-A.	f	2026-05-06 07:10:38.113845	34
357	38	assignment	New Assignment	Sample 1 has been posted for Batch-A.	f	2026-05-06 07:10:38.113846	34
\.


--
-- TOC entry 3763 (class 0 OID 122911)
-- Dependencies: 246
-- Data for Name: question_options; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.question_options (id, question_id, text, is_correct) FROM stdin;
1	1	Optifghgfhfghon 1	f
2	1	fghfgh	f
3	1	fgthfgh	f
4	1	hfghgfhgfh	f
5	2	Option 1	t
6	2	s	f
7	2	a	f
8	2	sa	f
9	3	Opasation 1	f
10	3	sas	f
11	4	Option 1	f
12	5	Option 1	f
13	6	Optiodn 1	f
14	6	sd	f
15	6	sd	f
16	6	dssdsd	f
17	7	Optionsfsfsf 1	f
18	7	ssfsf	f
19	7	fsfsfs	f
20	7	sfsfsfs	f
21	8	Optivbvbon 1	f
22	8	vbvb	f
23	8	bvbvb	f
24	8	vbvbvbvb	f
25	9	Optiocvcn 1	f
26	9	cvcv	f
27	9	cbtgh	f
28	9	rttrrt	f
29	10	Option 1	f
30	11	Option 1	f
31	12	q1	f
32	12	q	f
33	12	q	f
34	12	q	f
35	13	Option 1	f
36	14	Option 1	f
37	15	Option 1	f
\.


--
-- TOC entry 3753 (class 0 OID 98335)
-- Dependencies: 236
-- Data for Name: resources_module; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.resources_module (id, title, file_url, module_id) FROM stdin;
\.


--
-- TOC entry 3742 (class 0 OID 40998)
-- Dependencies: 225
-- Data for Name: session_participants; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.session_participants (id, session_id, user_id, join_time, leave_time, duration_minutes, status) FROM stdin;
\.


--
-- TOC entry 3767 (class 0 OID 131093)
-- Dependencies: 250
-- Data for Name: student_answers; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.student_answers (id, submission_id, question_id, selected_option_id) FROM stdin;
\.


--
-- TOC entry 3761 (class 0 OID 122896)
-- Dependencies: 244
-- Data for Name: test_questions; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.test_questions (id, test_id, text) FROM stdin;
1	3	1.hfghdfhfgh
2	4	xxxxxxxxxxxxxxxxa
3	4	aaaaaaaaaaaaaaaaaaaa
4	4	qqqqqqqqqqqqqqqqqqq
5	4	3333333333333333333333
6	5	sdsdsd
7	6	1.sfcasfsaf
8	7	asasasa
9	7	asadddddddddsasasasasa
10	7	rtrtrt
11	7	hhmnbnmbnbnbn
12	8	qqqqqqqqq
13	9	Asasasas
14	9	Asasas
15	9	Asasasa
\.


--
-- TOC entry 3765 (class 0 OID 131073)
-- Dependencies: 248
-- Data for Name: test_submissions; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.test_submissions (id, test_id, student_user_id, started_at, submitted_at, score, is_passed, status) FROM stdin;
1	1	7	2026-03-19 13:11:43.360194	\N	\N	\N	in_progress
\.


--
-- TOC entry 3759 (class 0 OID 122881)
-- Dependencies: 242
-- Data for Name: tests; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.tests (id, title, description, course_id, batch_name, module_name, start_time, end_time, created_at) FROM stdin;
1	string	\N	1	Batch-A	string	\N	\N	2026-03-17 11:44:53.132061
3	model	fgcfgfgfg	1	Batch-A	Frontier Engineering Techniques	2026-03-24 03:30:19.302	2026-03-24 04:30:19.302	2026-03-24 07:49:11.760546
4	aaaaaaa		1	Batch-A	Frontier Engineering Techniques	2026-03-25 06:30:34	2026-03-24 19:30:34	2026-03-24 07:51:41.026213
5	dfdgdfg		1	Batch-A	Frontier Engineering Techniques	2026-03-24 08:00:01.529	2026-03-23 20:30:01.529	2026-03-24 07:56:43.117305
6	model	edfdsfsdfdsfdsf	1	Batch-A	Frontier Engineering Techniques	2026-04-01 03:30:54.822	2026-04-01 04:30:54.822	2026-04-01 08:40:10.602079
7	Vishva	asasasasasasasa	1	Batch-A	Frontier Engineering Techniques	2026-04-01 09:05:44.066	2026-04-01 09:35:44.066	2026-04-01 09:04:37.735989
8	midsoles	qqqqqqqqqqq	1	Batch-A	Frontier Engineering Techniques	2026-04-01 03:30:57.966	2026-04-01 04:30:57.966	2026-04-01 09:54:43.055529
9	Assaassasas	Asasasas	1	Batch A	Introduction to AI & Machine Learning	2026-04-03 03:30:12.31	2026-04-03 04:30:12.31	2026-04-03 06:07:38.140739
\.


--
-- TOC entry 3757 (class 0 OID 98365)
-- Dependencies: 240
-- Data for Name: tests_module; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.tests_module (id, title, test_date, module_id) FROM stdin;
\.


--
-- TOC entry 3744 (class 0 OID 41004)
-- Dependencies: 227
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.users (id, name, email, password_hash, role, student_id) FROM stdin;
6	instructor	instructor@coirei.com	$2b$12$b7oPDclRrwSW9sAOAnk7H.z0qjvggSPk8fgOj4FmYBLksmYurgaFy	instructor	\N
7	Kuberan	kuberan@coirei.com	$2b$12$SxylNebePVvMKDLt4rFwduGUCBE8180XjMxEpRMaWRox1PbF.mjp2	student	\N
20	Swathi  P	swathipugazhendhi04@gmail.com	$2b$12$0/kxyp11Q7Ajo0tp82NgvOv1DDGWc7oQYVT4l7erWzJ4FYxOFVmMK	student	AF001
21	Jenifer S	jenic4e@gmail.com	$2b$12$H7eTyJLlBcqaMUaa5OIhHeCBACNTHQUZAyQjx2Ug36RQPW2GbJNjW	student	AF002
22	Jelutshiya M	jelutshiyam@gmail.com	$2b$12$IhDTRGX3tcaW28nDADLreeVMYi.Kqe0X9l7P8blYkYHja0IpS9nyW	student	AF003
23	papishetty deekshith	pdeekshith622@gmail.com	$2b$12$K5cWCUaZg5qKWzx5gr.VqeFcy9W2SMTJtleGZfK0yazIOVTE/Iiku	student	AF004
24	PIYUSH SAMUDRALA	Samudralapiyush@gmail.com	$2b$12$TicRbkb4n6kk9VvsxH7UNurgA1Cnq.6iQV19J2hr4a3j8nXAA90OK	student	AF005
25	manju Bhargav  B	bikkumallamanjubhargav@gmail.com	$2b$12$paMsv35Oy9LdzsIM0hy5retlTfZA/Xn.wOzGS1aGpjhwmcYfsF8A6	student	AF006
26	Priyan chakkaravarthi	Priyanchakkaravarthir@gmail.com	$2b$12$YTquKcOYLCNvcdkSvQkmG.XnqUNzGYJ.sAD0Ce.XclrVwbA2iicNu	student	AF007
27	srikar 	srikar1121@gmail.com	$2b$12$xpq7iROLm67MzIN74t7rYOhj5Ol4I4BGlvBSvzmaLEXAUqJsVCKum	student	AF008
28	Siva manikanta  reddy	sivamanikantareddytatiparthi3@gmail.com	$2b$12$k4ev7S9zgx/9Za7ojmU8nu.3LPSPg0Drq28vCazyMu9DwnvFZZZ.O	student	AF009
29	Jayashree  Abhinaya 	jayashree.abhinaya.92@gmail.com	$2b$12$pP.oY9SAlDD6rbLWBpy9AO8or2W.CuvVD042pkvrWPRUNwpt48bMi	student	AF010
30	Niranjan  	niranjanadiga1989@gmail.com	$2b$12$g8dH68Is9/uHsT4GWhTb4.kdlDIpWNDYPjyg7/oQdZcpQ4RHgqyIO	student	AF011
33	niranjan	niranjanadiga@gmail.com	$2b$12$gx0uBDyY7yZsj6tm2TX74uSdoF6fuw8AhyZAmZC9O/Vjt68LGtUqa	instructor	\N
34	Nagulesh  R	nagulesh270@gmail.com	$2b$12$yI.Fq2zRoLMfxwqFoZNIvu8VhJW/KbQ/B8sbAICbKJr2rgDreNaIG	student	AF012
35	Pandiprajin s	pandiprajin161207@gmail.com	$2b$12$i5v2xZRnkishL0UaYZvoWumIdQ9b9CED4tkYie9O4Go9j65jfX29S	student	AF013
36	Hariharan  R	hariharan2528ht@gmail.com	$2b$12$bkTYiP6Y1inMWT21r5H3luRvM/7/OCXM7VCjt/3pHh5XsRznG4sZW	student	AF014
37	Vigrah  S	vigrah2611@gmail.com	$2b$12$XYXxKCDG82Za7iioTWMLI.aAnvblmlD.wlr0Gk3zE3c/9X8pGkFdq	student	AF015
38	Sarath M	Sarathbabu113@gmail.com	$2b$12$CDByY86jHS/vh9D3yL1MWu2KrE.MZ0M5NcwXNfkkm7aFFU7K7PIJe	student	AF016
\.


--
-- TOC entry 3844 (class 0 OID 0)
-- Dependencies: 253
-- Name: assignment_resources_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.assignment_resources_id_seq', 12, true);


--
-- TOC entry 3845 (class 0 OID 0)
-- Dependencies: 255
-- Name: assignment_submissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.assignment_submissions_id_seq', 9, true);


--
-- TOC entry 3846 (class 0 OID 0)
-- Dependencies: 251
-- Name: assignments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.assignments_id_seq', 34, true);


--
-- TOC entry 3847 (class 0 OID 0)
-- Dependencies: 237
-- Name: assignments_module_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.assignments_module_id_seq', 1, false);


--
-- TOC entry 3848 (class 0 OID 0)
-- Dependencies: 233
-- Name: chapters_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.chapters_id_seq', 4, true);


--
-- TOC entry 3849 (class 0 OID 0)
-- Dependencies: 263
-- Name: chat_bookmarks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.chat_bookmarks_id_seq', 1, false);


--
-- TOC entry 3850 (class 0 OID 0)
-- Dependencies: 261
-- Name: chat_likes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.chat_likes_id_seq', 1, false);


--
-- TOC entry 3851 (class 0 OID 0)
-- Dependencies: 257
-- Name: chat_posts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.chat_posts_id_seq', 2, true);


--
-- TOC entry 3852 (class 0 OID 0)
-- Dependencies: 259
-- Name: chat_replies_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.chat_replies_id_seq', 1, true);


--
-- TOC entry 3853 (class 0 OID 0)
-- Dependencies: 269
-- Name: chat_reply_likes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.chat_reply_likes_id_seq', 1, false);


--
-- TOC entry 3854 (class 0 OID 0)
-- Dependencies: 218
-- Name: class_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.class_sessions_id_seq', 13, true);


--
-- TOC entry 3855 (class 0 OID 0)
-- Dependencies: 220
-- Name: classrooms_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.classrooms_id_seq', 1, true);


--
-- TOC entry 3856 (class 0 OID 0)
-- Dependencies: 229
-- Name: course_schedules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.course_schedules_id_seq', 1, false);


--
-- TOC entry 3857 (class 0 OID 0)
-- Dependencies: 222
-- Name: courses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.courses_id_seq', 1, true);


--
-- TOC entry 3858 (class 0 OID 0)
-- Dependencies: 271
-- Name: dm_conversations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.dm_conversations_id_seq', 1, false);


--
-- TOC entry 3859 (class 0 OID 0)
-- Dependencies: 281
-- Name: dm_message_bookmarks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.dm_message_bookmarks_id_seq', 1, false);


--
-- TOC entry 3860 (class 0 OID 0)
-- Dependencies: 279
-- Name: dm_message_likes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.dm_message_likes_id_seq', 1, false);


--
-- TOC entry 3861 (class 0 OID 0)
-- Dependencies: 275
-- Name: dm_messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.dm_messages_id_seq', 1, false);


--
-- TOC entry 3862 (class 0 OID 0)
-- Dependencies: 224
-- Name: enrollments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.enrollments_id_seq', 17, true);


--
-- TOC entry 3863 (class 0 OID 0)
-- Dependencies: 273
-- Name: group_chats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.group_chats_id_seq', 1, false);


--
-- TOC entry 3864 (class 0 OID 0)
-- Dependencies: 285
-- Name: group_message_bookmarks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.group_message_bookmarks_id_seq', 1, false);


--
-- TOC entry 3865 (class 0 OID 0)
-- Dependencies: 283
-- Name: group_message_likes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.group_message_likes_id_seq', 1, false);


--
-- TOC entry 3866 (class 0 OID 0)
-- Dependencies: 277
-- Name: group_messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.group_messages_id_seq', 1, false);


--
-- TOC entry 3867 (class 0 OID 0)
-- Dependencies: 267
-- Name: instructor_enrollments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.instructor_enrollments_id_seq', 1, false);


--
-- TOC entry 3868 (class 0 OID 0)
-- Dependencies: 231
-- Name: modules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.modules_id_seq', 2, true);


--
-- TOC entry 3869 (class 0 OID 0)
-- Dependencies: 265
-- Name: notifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.notifications_id_seq', 357, true);


--
-- TOC entry 3870 (class 0 OID 0)
-- Dependencies: 245
-- Name: question_options_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.question_options_id_seq', 37, true);


--
-- TOC entry 3871 (class 0 OID 0)
-- Dependencies: 235
-- Name: resources_module_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.resources_module_id_seq', 1, false);


--
-- TOC entry 3872 (class 0 OID 0)
-- Dependencies: 226
-- Name: session_participants_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.session_participants_id_seq', 1120, true);


--
-- TOC entry 3873 (class 0 OID 0)
-- Dependencies: 249
-- Name: student_answers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.student_answers_id_seq', 1, false);


--
-- TOC entry 3874 (class 0 OID 0)
-- Dependencies: 243
-- Name: test_questions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.test_questions_id_seq', 15, true);


--
-- TOC entry 3875 (class 0 OID 0)
-- Dependencies: 247
-- Name: test_submissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.test_submissions_id_seq', 1, true);


--
-- TOC entry 3876 (class 0 OID 0)
-- Dependencies: 241
-- Name: tests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.tests_id_seq', 10, true);


--
-- TOC entry 3877 (class 0 OID 0)
-- Dependencies: 239
-- Name: tests_module_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.tests_module_id_seq', 1, false);


--
-- TOC entry 3878 (class 0 OID 0)
-- Dependencies: 228
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.users_id_seq', 38, true);


--
-- TOC entry 3471 (class 2606 OID 139292)
-- Name: assignment_resources assignment_resources_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.assignment_resources
    ADD CONSTRAINT assignment_resources_pkey PRIMARY KEY (id);


--
-- TOC entry 3474 (class 2606 OID 139307)
-- Name: assignment_submissions assignment_submissions_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.assignment_submissions
    ADD CONSTRAINT assignment_submissions_pkey PRIMARY KEY (id);


--
-- TOC entry 3447 (class 2606 OID 98357)
-- Name: assignments_module assignments_module_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.assignments_module
    ADD CONSTRAINT assignments_module_pkey PRIMARY KEY (id);


--
-- TOC entry 3468 (class 2606 OID 139272)
-- Name: assignments assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.assignments
    ADD CONSTRAINT assignments_pkey PRIMARY KEY (id);


--
-- TOC entry 3441 (class 2606 OID 98327)
-- Name: chapters chapters_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.chapters
    ADD CONSTRAINT chapters_pkey PRIMARY KEY (id);


--
-- TOC entry 3486 (class 2606 OID 147520)
-- Name: chat_bookmarks chat_bookmarks_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.chat_bookmarks
    ADD CONSTRAINT chat_bookmarks_pkey PRIMARY KEY (id);


--
-- TOC entry 3483 (class 2606 OID 147502)
-- Name: chat_likes chat_likes_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.chat_likes
    ADD CONSTRAINT chat_likes_pkey PRIMARY KEY (id);


--
-- TOC entry 3477 (class 2606 OID 147464)
-- Name: chat_posts chat_posts_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.chat_posts
    ADD CONSTRAINT chat_posts_pkey PRIMARY KEY (id);


--
-- TOC entry 3480 (class 2606 OID 147484)
-- Name: chat_replies chat_replies_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.chat_replies
    ADD CONSTRAINT chat_replies_pkey PRIMARY KEY (id);


--
-- TOC entry 3497 (class 2606 OID 188422)
-- Name: chat_reply_likes chat_reply_likes_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.chat_reply_likes
    ADD CONSTRAINT chat_reply_likes_pkey PRIMARY KEY (id);


--
-- TOC entry 3418 (class 2606 OID 41017)
-- Name: class_sessions class_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.class_sessions
    ADD CONSTRAINT class_sessions_pkey PRIMARY KEY (id);


--
-- TOC entry 3420 (class 2606 OID 41019)
-- Name: classrooms classrooms_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.classrooms
    ADD CONSTRAINT classrooms_pkey PRIMARY KEY (id);


--
-- TOC entry 3422 (class 2606 OID 41021)
-- Name: classrooms classrooms_room_name_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.classrooms
    ADD CONSTRAINT classrooms_room_name_key UNIQUE (room_name);


--
-- TOC entry 3436 (class 2606 OID 90120)
-- Name: course_schedules course_schedules_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.course_schedules
    ADD CONSTRAINT course_schedules_pkey PRIMARY KEY (id);


--
-- TOC entry 3424 (class 2606 OID 41023)
-- Name: courses courses_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.courses
    ADD CONSTRAINT courses_pkey PRIMARY KEY (id);


--
-- TOC entry 3500 (class 2606 OID 188440)
-- Name: dm_conversations dm_conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.dm_conversations
    ADD CONSTRAINT dm_conversations_pkey PRIMARY KEY (id);


--
-- TOC entry 3521 (class 2606 OID 188537)
-- Name: dm_message_bookmarks dm_message_bookmarks_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.dm_message_bookmarks
    ADD CONSTRAINT dm_message_bookmarks_pkey PRIMARY KEY (id);


--
-- TOC entry 3516 (class 2606 OID 188517)
-- Name: dm_message_likes dm_message_likes_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.dm_message_likes
    ADD CONSTRAINT dm_message_likes_pkey PRIMARY KEY (id);


--
-- TOC entry 3510 (class 2606 OID 188479)
-- Name: dm_messages dm_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.dm_messages
    ADD CONSTRAINT dm_messages_pkey PRIMARY KEY (id);


--
-- TOC entry 3426 (class 2606 OID 41025)
-- Name: enrollments enrollments_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.enrollments
    ADD CONSTRAINT enrollments_pkey PRIMARY KEY (id);


--
-- TOC entry 3505 (class 2606 OID 188462)
-- Name: group_chats group_chats_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.group_chats
    ADD CONSTRAINT group_chats_pkey PRIMARY KEY (id);


--
-- TOC entry 3531 (class 2606 OID 188577)
-- Name: group_message_bookmarks group_message_bookmarks_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.group_message_bookmarks
    ADD CONSTRAINT group_message_bookmarks_pkey PRIMARY KEY (id);


--
-- TOC entry 3526 (class 2606 OID 188557)
-- Name: group_message_likes group_message_likes_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.group_message_likes
    ADD CONSTRAINT group_message_likes_pkey PRIMARY KEY (id);


--
-- TOC entry 3513 (class 2606 OID 188499)
-- Name: group_messages group_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.group_messages
    ADD CONSTRAINT group_messages_pkey PRIMARY KEY (id);


--
-- TOC entry 3493 (class 2606 OID 180232)
-- Name: instructor_enrollments instructor_enrollments_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.instructor_enrollments
    ADD CONSTRAINT instructor_enrollments_pkey PRIMARY KEY (id);


--
-- TOC entry 3439 (class 2606 OID 98312)
-- Name: modules modules_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.modules
    ADD CONSTRAINT modules_pkey PRIMARY KEY (id);


--
-- TOC entry 3491 (class 2606 OID 172040)
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- TOC entry 3460 (class 2606 OID 122918)
-- Name: question_options question_options_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.question_options
    ADD CONSTRAINT question_options_pkey PRIMARY KEY (id);


--
-- TOC entry 3445 (class 2606 OID 98342)
-- Name: resources_module resources_module_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.resources_module
    ADD CONSTRAINT resources_module_pkey PRIMARY KEY (id);


--
-- TOC entry 3428 (class 2606 OID 41027)
-- Name: session_participants session_participants_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.session_participants
    ADD CONSTRAINT session_participants_pkey PRIMARY KEY (id);


--
-- TOC entry 3466 (class 2606 OID 131098)
-- Name: student_answers student_answers_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.student_answers
    ADD CONSTRAINT student_answers_pkey PRIMARY KEY (id);


--
-- TOC entry 3457 (class 2606 OID 122903)
-- Name: test_questions test_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.test_questions
    ADD CONSTRAINT test_questions_pkey PRIMARY KEY (id);


--
-- TOC entry 3463 (class 2606 OID 131080)
-- Name: test_submissions test_submissions_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.test_submissions
    ADD CONSTRAINT test_submissions_pkey PRIMARY KEY (id);


--
-- TOC entry 3451 (class 2606 OID 98372)
-- Name: tests_module tests_module_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tests_module
    ADD CONSTRAINT tests_module_pkey PRIMARY KEY (id);


--
-- TOC entry 3454 (class 2606 OID 122888)
-- Name: tests tests_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tests
    ADD CONSTRAINT tests_pkey PRIMARY KEY (id);


--
-- TOC entry 3524 (class 2606 OID 188539)
-- Name: dm_message_bookmarks uq_dm_bookmark; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.dm_message_bookmarks
    ADD CONSTRAINT uq_dm_bookmark UNIQUE (message_id, user_id);


--
-- TOC entry 3519 (class 2606 OID 188519)
-- Name: dm_message_likes uq_dm_like; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.dm_message_likes
    ADD CONSTRAINT uq_dm_like UNIQUE (message_id, user_id);


--
-- TOC entry 3503 (class 2606 OID 188442)
-- Name: dm_conversations uq_dm_pair; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.dm_conversations
    ADD CONSTRAINT uq_dm_pair UNIQUE (user_a_id, user_b_id);


--
-- TOC entry 3534 (class 2606 OID 188579)
-- Name: group_message_bookmarks uq_group_bookmark; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.group_message_bookmarks
    ADD CONSTRAINT uq_group_bookmark UNIQUE (message_id, user_id);


--
-- TOC entry 3508 (class 2606 OID 188464)
-- Name: group_chats uq_group_chat; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.group_chats
    ADD CONSTRAINT uq_group_chat UNIQUE (course_id, batch_name);


--
-- TOC entry 3529 (class 2606 OID 188559)
-- Name: group_message_likes uq_group_like; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.group_message_likes
    ADD CONSTRAINT uq_group_like UNIQUE (message_id, user_id);


--
-- TOC entry 3495 (class 2606 OID 180234)
-- Name: instructor_enrollments uq_instructor_course_batch; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.instructor_enrollments
    ADD CONSTRAINT uq_instructor_course_batch UNIQUE (user_id, course_id, batch_name);


--
-- TOC entry 3430 (class 2606 OID 41029)
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- TOC entry 3432 (class 2606 OID 41031)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 3434 (class 2606 OID 81921)
-- Name: users users_student_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_student_id_key UNIQUE (student_id);


--
-- TOC entry 3472 (class 1259 OID 139298)
-- Name: ix_assignment_resources_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_assignment_resources_id ON public.assignment_resources USING btree (id);


--
-- TOC entry 3475 (class 1259 OID 139318)
-- Name: ix_assignment_submissions_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_assignment_submissions_id ON public.assignment_submissions USING btree (id);


--
-- TOC entry 3469 (class 1259 OID 139283)
-- Name: ix_assignments_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_assignments_id ON public.assignments USING btree (id);


--
-- TOC entry 3448 (class 1259 OID 98363)
-- Name: ix_assignments_module_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_assignments_module_id ON public.assignments_module USING btree (id);


--
-- TOC entry 3442 (class 1259 OID 98333)
-- Name: ix_chapters_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_chapters_id ON public.chapters USING btree (id);


--
-- TOC entry 3487 (class 1259 OID 147531)
-- Name: ix_chat_bookmarks_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_chat_bookmarks_id ON public.chat_bookmarks USING btree (id);


--
-- TOC entry 3484 (class 1259 OID 147513)
-- Name: ix_chat_likes_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_chat_likes_id ON public.chat_likes USING btree (id);


--
-- TOC entry 3478 (class 1259 OID 147475)
-- Name: ix_chat_posts_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_chat_posts_id ON public.chat_posts USING btree (id);


--
-- TOC entry 3481 (class 1259 OID 147495)
-- Name: ix_chat_replies_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_chat_replies_id ON public.chat_replies USING btree (id);


--
-- TOC entry 3498 (class 1259 OID 188433)
-- Name: ix_chat_reply_likes_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_chat_reply_likes_id ON public.chat_reply_likes USING btree (id);


--
-- TOC entry 3501 (class 1259 OID 188453)
-- Name: ix_dm_conversations_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_dm_conversations_id ON public.dm_conversations USING btree (id);


--
-- TOC entry 3522 (class 1259 OID 188550)
-- Name: ix_dm_message_bookmarks_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_dm_message_bookmarks_id ON public.dm_message_bookmarks USING btree (id);


--
-- TOC entry 3517 (class 1259 OID 188530)
-- Name: ix_dm_message_likes_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_dm_message_likes_id ON public.dm_message_likes USING btree (id);


--
-- TOC entry 3511 (class 1259 OID 188490)
-- Name: ix_dm_messages_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_dm_messages_id ON public.dm_messages USING btree (id);


--
-- TOC entry 3506 (class 1259 OID 188470)
-- Name: ix_group_chats_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_group_chats_id ON public.group_chats USING btree (id);


--
-- TOC entry 3532 (class 1259 OID 188590)
-- Name: ix_group_message_bookmarks_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_group_message_bookmarks_id ON public.group_message_bookmarks USING btree (id);


--
-- TOC entry 3527 (class 1259 OID 188570)
-- Name: ix_group_message_likes_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_group_message_likes_id ON public.group_message_likes USING btree (id);


--
-- TOC entry 3514 (class 1259 OID 188510)
-- Name: ix_group_messages_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_group_messages_id ON public.group_messages USING btree (id);


--
-- TOC entry 3437 (class 1259 OID 98318)
-- Name: ix_modules_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_modules_id ON public.modules USING btree (id);


--
-- TOC entry 3488 (class 1259 OID 172047)
-- Name: ix_notifications_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_notifications_id ON public.notifications USING btree (id);


--
-- TOC entry 3489 (class 1259 OID 172046)
-- Name: ix_notifications_user_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_notifications_user_id ON public.notifications USING btree (user_id);


--
-- TOC entry 3458 (class 1259 OID 122924)
-- Name: ix_question_options_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_question_options_id ON public.question_options USING btree (id);


--
-- TOC entry 3443 (class 1259 OID 98348)
-- Name: ix_resources_module_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_resources_module_id ON public.resources_module USING btree (id);


--
-- TOC entry 3464 (class 1259 OID 131114)
-- Name: ix_student_answers_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_student_answers_id ON public.student_answers USING btree (id);


--
-- TOC entry 3455 (class 1259 OID 122909)
-- Name: ix_test_questions_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_test_questions_id ON public.test_questions USING btree (id);


--
-- TOC entry 3461 (class 1259 OID 131091)
-- Name: ix_test_submissions_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_test_submissions_id ON public.test_submissions USING btree (id);


--
-- TOC entry 3452 (class 1259 OID 122894)
-- Name: ix_tests_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_tests_id ON public.tests USING btree (id);


--
-- TOC entry 3449 (class 1259 OID 98378)
-- Name: ix_tests_module_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX ix_tests_module_id ON public.tests_module USING btree (id);


--
-- TOC entry 3558 (class 2606 OID 139293)
-- Name: assignment_resources assignment_resources_assignment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.assignment_resources
    ADD CONSTRAINT assignment_resources_assignment_id_fkey FOREIGN KEY (assignment_id) REFERENCES public.assignments(id);


--
-- TOC entry 3559 (class 2606 OID 139308)
-- Name: assignment_submissions assignment_submissions_assignment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.assignment_submissions
    ADD CONSTRAINT assignment_submissions_assignment_id_fkey FOREIGN KEY (assignment_id) REFERENCES public.assignments(id);


--
-- TOC entry 3560 (class 2606 OID 139313)
-- Name: assignment_submissions assignment_submissions_student_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.assignment_submissions
    ADD CONSTRAINT assignment_submissions_student_user_id_fkey FOREIGN KEY (student_user_id) REFERENCES public.users(id);


--
-- TOC entry 3556 (class 2606 OID 139273)
-- Name: assignments assignments_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.assignments
    ADD CONSTRAINT assignments_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id);


--
-- TOC entry 3557 (class 2606 OID 139278)
-- Name: assignments assignments_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.assignments
    ADD CONSTRAINT assignments_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- TOC entry 3546 (class 2606 OID 98358)
-- Name: assignments_module assignments_module_module_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.assignments_module
    ADD CONSTRAINT assignments_module_module_id_fkey FOREIGN KEY (module_id) REFERENCES public.modules(id);


--
-- TOC entry 3544 (class 2606 OID 98328)
-- Name: chapters chapters_module_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.chapters
    ADD CONSTRAINT chapters_module_id_fkey FOREIGN KEY (module_id) REFERENCES public.modules(id);


--
-- TOC entry 3567 (class 2606 OID 147521)
-- Name: chat_bookmarks chat_bookmarks_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.chat_bookmarks
    ADD CONSTRAINT chat_bookmarks_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.chat_posts(id);


--
-- TOC entry 3568 (class 2606 OID 147526)
-- Name: chat_bookmarks chat_bookmarks_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.chat_bookmarks
    ADD CONSTRAINT chat_bookmarks_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3565 (class 2606 OID 147503)
-- Name: chat_likes chat_likes_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.chat_likes
    ADD CONSTRAINT chat_likes_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.chat_posts(id);


--
-- TOC entry 3566 (class 2606 OID 147508)
-- Name: chat_likes chat_likes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.chat_likes
    ADD CONSTRAINT chat_likes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3561 (class 2606 OID 147470)
-- Name: chat_posts chat_posts_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.chat_posts
    ADD CONSTRAINT chat_posts_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.users(id);


--
-- TOC entry 3562 (class 2606 OID 147465)
-- Name: chat_posts chat_posts_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.chat_posts
    ADD CONSTRAINT chat_posts_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id);


--
-- TOC entry 3563 (class 2606 OID 147490)
-- Name: chat_replies chat_replies_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.chat_replies
    ADD CONSTRAINT chat_replies_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.users(id);


--
-- TOC entry 3564 (class 2606 OID 147485)
-- Name: chat_replies chat_replies_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.chat_replies
    ADD CONSTRAINT chat_replies_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.chat_posts(id);


--
-- TOC entry 3572 (class 2606 OID 188423)
-- Name: chat_reply_likes chat_reply_likes_reply_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.chat_reply_likes
    ADD CONSTRAINT chat_reply_likes_reply_id_fkey FOREIGN KEY (reply_id) REFERENCES public.chat_replies(id);


--
-- TOC entry 3573 (class 2606 OID 188428)
-- Name: chat_reply_likes chat_reply_likes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.chat_reply_likes
    ADD CONSTRAINT chat_reply_likes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3535 (class 2606 OID 41032)
-- Name: class_sessions class_sessions_classroom_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.class_sessions
    ADD CONSTRAINT class_sessions_classroom_id_fkey FOREIGN KEY (classroom_id) REFERENCES public.classrooms(id);


--
-- TOC entry 3537 (class 2606 OID 57344)
-- Name: classrooms classrooms_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.classrooms
    ADD CONSTRAINT classrooms_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id);


--
-- TOC entry 3542 (class 2606 OID 90121)
-- Name: course_schedules course_schedules_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.course_schedules
    ADD CONSTRAINT course_schedules_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id);


--
-- TOC entry 3574 (class 2606 OID 188443)
-- Name: dm_conversations dm_conversations_user_a_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.dm_conversations
    ADD CONSTRAINT dm_conversations_user_a_id_fkey FOREIGN KEY (user_a_id) REFERENCES public.users(id);


--
-- TOC entry 3575 (class 2606 OID 188448)
-- Name: dm_conversations dm_conversations_user_b_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.dm_conversations
    ADD CONSTRAINT dm_conversations_user_b_id_fkey FOREIGN KEY (user_b_id) REFERENCES public.users(id);


--
-- TOC entry 3583 (class 2606 OID 188540)
-- Name: dm_message_bookmarks dm_message_bookmarks_message_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.dm_message_bookmarks
    ADD CONSTRAINT dm_message_bookmarks_message_id_fkey FOREIGN KEY (message_id) REFERENCES public.dm_messages(id);


--
-- TOC entry 3584 (class 2606 OID 188545)
-- Name: dm_message_bookmarks dm_message_bookmarks_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.dm_message_bookmarks
    ADD CONSTRAINT dm_message_bookmarks_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3581 (class 2606 OID 188520)
-- Name: dm_message_likes dm_message_likes_message_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.dm_message_likes
    ADD CONSTRAINT dm_message_likes_message_id_fkey FOREIGN KEY (message_id) REFERENCES public.dm_messages(id);


--
-- TOC entry 3582 (class 2606 OID 188525)
-- Name: dm_message_likes dm_message_likes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.dm_message_likes
    ADD CONSTRAINT dm_message_likes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3577 (class 2606 OID 188480)
-- Name: dm_messages dm_messages_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.dm_messages
    ADD CONSTRAINT dm_messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.dm_conversations(id);


--
-- TOC entry 3578 (class 2606 OID 188485)
-- Name: dm_messages dm_messages_sender_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.dm_messages
    ADD CONSTRAINT dm_messages_sender_id_fkey FOREIGN KEY (sender_id) REFERENCES public.users(id);


--
-- TOC entry 3536 (class 2606 OID 65536)
-- Name: class_sessions fk_class_sessions_course; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.class_sessions
    ADD CONSTRAINT fk_class_sessions_course FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE CASCADE;


--
-- TOC entry 3538 (class 2606 OID 41037)
-- Name: enrollments fk_course; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.enrollments
    ADD CONSTRAINT fk_course FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE CASCADE;


--
-- TOC entry 3539 (class 2606 OID 49152)
-- Name: enrollments fk_enrollment_classroom; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.enrollments
    ADD CONSTRAINT fk_enrollment_classroom FOREIGN KEY (classroom_id) REFERENCES public.classrooms(id) ON DELETE CASCADE;


--
-- TOC entry 3540 (class 2606 OID 41042)
-- Name: enrollments fk_user; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.enrollments
    ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 3576 (class 2606 OID 188465)
-- Name: group_chats group_chats_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.group_chats
    ADD CONSTRAINT group_chats_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id);


--
-- TOC entry 3587 (class 2606 OID 188580)
-- Name: group_message_bookmarks group_message_bookmarks_message_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.group_message_bookmarks
    ADD CONSTRAINT group_message_bookmarks_message_id_fkey FOREIGN KEY (message_id) REFERENCES public.group_messages(id);


--
-- TOC entry 3588 (class 2606 OID 188585)
-- Name: group_message_bookmarks group_message_bookmarks_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.group_message_bookmarks
    ADD CONSTRAINT group_message_bookmarks_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3585 (class 2606 OID 188560)
-- Name: group_message_likes group_message_likes_message_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.group_message_likes
    ADD CONSTRAINT group_message_likes_message_id_fkey FOREIGN KEY (message_id) REFERENCES public.group_messages(id);


--
-- TOC entry 3586 (class 2606 OID 188565)
-- Name: group_message_likes group_message_likes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.group_message_likes
    ADD CONSTRAINT group_message_likes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3579 (class 2606 OID 188500)
-- Name: group_messages group_messages_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.group_messages
    ADD CONSTRAINT group_messages_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.group_chats(id);


--
-- TOC entry 3580 (class 2606 OID 188505)
-- Name: group_messages group_messages_sender_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.group_messages
    ADD CONSTRAINT group_messages_sender_id_fkey FOREIGN KEY (sender_id) REFERENCES public.users(id);


--
-- TOC entry 3570 (class 2606 OID 180240)
-- Name: instructor_enrollments instructor_enrollments_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.instructor_enrollments
    ADD CONSTRAINT instructor_enrollments_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id);


--
-- TOC entry 3571 (class 2606 OID 180235)
-- Name: instructor_enrollments instructor_enrollments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.instructor_enrollments
    ADD CONSTRAINT instructor_enrollments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3543 (class 2606 OID 98313)
-- Name: modules modules_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.modules
    ADD CONSTRAINT modules_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id);


--
-- TOC entry 3569 (class 2606 OID 172041)
-- Name: notifications notifications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 3550 (class 2606 OID 122919)
-- Name: question_options question_options_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.question_options
    ADD CONSTRAINT question_options_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.test_questions(id);


--
-- TOC entry 3545 (class 2606 OID 98343)
-- Name: resources_module resources_module_module_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.resources_module
    ADD CONSTRAINT resources_module_module_id_fkey FOREIGN KEY (module_id) REFERENCES public.modules(id);


--
-- TOC entry 3541 (class 2606 OID 41047)
-- Name: session_participants session_participants_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.session_participants
    ADD CONSTRAINT session_participants_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.class_sessions(id);


--
-- TOC entry 3553 (class 2606 OID 131104)
-- Name: student_answers student_answers_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.student_answers
    ADD CONSTRAINT student_answers_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.test_questions(id);


--
-- TOC entry 3554 (class 2606 OID 131109)
-- Name: student_answers student_answers_selected_option_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.student_answers
    ADD CONSTRAINT student_answers_selected_option_id_fkey FOREIGN KEY (selected_option_id) REFERENCES public.question_options(id);


--
-- TOC entry 3555 (class 2606 OID 131099)
-- Name: student_answers student_answers_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.student_answers
    ADD CONSTRAINT student_answers_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES public.test_submissions(id);


--
-- TOC entry 3549 (class 2606 OID 122904)
-- Name: test_questions test_questions_test_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.test_questions
    ADD CONSTRAINT test_questions_test_id_fkey FOREIGN KEY (test_id) REFERENCES public.tests(id);


--
-- TOC entry 3551 (class 2606 OID 131086)
-- Name: test_submissions test_submissions_student_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.test_submissions
    ADD CONSTRAINT test_submissions_student_user_id_fkey FOREIGN KEY (student_user_id) REFERENCES public.users(id);


--
-- TOC entry 3552 (class 2606 OID 131081)
-- Name: test_submissions test_submissions_test_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.test_submissions
    ADD CONSTRAINT test_submissions_test_id_fkey FOREIGN KEY (test_id) REFERENCES public.tests(id);


--
-- TOC entry 3548 (class 2606 OID 122889)
-- Name: tests tests_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tests
    ADD CONSTRAINT tests_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id);


--
-- TOC entry 3547 (class 2606 OID 98373)
-- Name: tests_module tests_module_module_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tests_module
    ADD CONSTRAINT tests_module_module_id_fkey FOREIGN KEY (module_id) REFERENCES public.modules(id);


--
-- TOC entry 2215 (class 826 OID 16394)
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT ALL ON SEQUENCES TO neon_superuser WITH GRANT OPTION;


--
-- TOC entry 2214 (class 826 OID 16393)
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT ALL ON TABLES TO neon_superuser WITH GRANT OPTION;


-- Completed on 2026-05-11 14:13:01

--
-- PostgreSQL database dump complete
--

\unrestrict mWSJWcdTdfVlnZnQyZkTnsoT1yvtmwvDtdDgOmMbTF7PEaBLIoOqTNWefFE7MDj

