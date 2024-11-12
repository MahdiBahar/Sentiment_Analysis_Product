BEGIN;
-- start

CREATE TABLE IF NOT EXISTS public.app_info
(
    app_id serial NOT NULL,
    app_name character varying(255) COLLATE pg_catalog."default",
    app_img text,
    app_name_company character varying(255),
    app_version character varying(100),
    app_total_rate character varying(50),
    app_average_rate character varying(50),
    app_install character varying(50),
    app_category character varying(200),
    app_size character varying(50),
    app_last_update text,
    UNIQUE (app_name), -- to solve the problem in recording once
    CONSTRAINT apps_pkey PRIMARY KEY (app_id)
);

CREATE TABLE IF NOT EXISTS public.comment
(
    comment_id serial NOT NULL,
    app_id integer,
    user_name character varying(255),
    user_image text,
    comment_text text,
    comment_rating numeric(2, 1),
    comment_date date,
    sentiment_result character varying(255),
    sentiment_processed boolean,
    PRIMARY KEY (comment_id)
);

CREATE TABLE IF NOT EXISTS public.stop_words
(
    stopword_id serial NOT NULL,
    app_id integer,
    stopword text,
    PRIMARY KEY (stopword_id)
);

CREATE TABLE IF NOT EXISTS public.sentiment_model
(
    model_id serial NOT NULL,
    model_name character varying(255),
    model_version character varying(50),
    last_update date,
    PRIMARY KEY (model_id)
);

CREATE TABLE IF NOT EXISTS public.processing_logs
(
    log_id serial NOT NULL,
    comment_id integer,
    model_id integer,
    sentiment character varying(255),
    processing_date timestamp with time zone,
    status character varying(50),
    PRIMARY KEY (log_id)
);

CREATE TABLE IF NOT EXISTS public.url_to_crawl
(
    crawl_app_id serial NOT NULL,
    crawl_app_name character varying(255),
    crawl_url text,
    PRIMARY KEY (crawl_app_id)
);


ALTER TABLE IF EXISTS public.comment
    ADD FOREIGN KEY (app_id)
    REFERENCES public.app_info (app_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;


ALTER TABLE IF EXISTS public.stop_words
    ADD FOREIGN KEY (app_id)
    REFERENCES public.app_info (app_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;


ALTER TABLE IF EXISTS public.processing_logs
    ADD FOREIGN KEY (comment_id)
    REFERENCES public.comment (comment_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;


ALTER TABLE IF EXISTS public.processing_logs
    ADD FOREIGN KEY (model_id)
    REFERENCES public.sentiment_model (model_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;


-- Initial URL entry
INSERT INTO public.url_to_crawl (crawl_app_name, crawl_url) VALUES
('HamrahBankMellat', 'https://cafebazaar.ir/app/com.pmb.mobile?l=fa'),
('MegaBank', 'https://cafebazaar.ir/app/com.bpm.social?l=fa'),
('‌Bale', 'https://cafebazaar.ir/app/ir.nasim?l=fa'),
('BluBank', 'https://cafebazaar.ir/app/com.samanpr.blu?l=fa'),
('Wepod', 'https://cafebazaar.ir/app/com.dotin.wepod?l=fa'),
('Bankino', 'https://cafebazaar.ir/app/digital.neobank?l=fa'),
('Bam', 'https://cafebazaar.ir/app/ir.bmi.bam.nativeweb?l=fa'),
('Mehr', 'https://cafebazaar.ir/app/com.ada.mbank.mehr?l=fa'),
('Shahr', 'https://cafebazaar.ir/app/com.citydi.hplus?l=fa'),
('Parsian', 'https://cafebazaar.ir/app/com.parsmobapp?l=fa'),
('Day', 'https://cafebazaar.ir/app/com.tosan.dara.day?l=fa'),
('Saman', 'https://cafebazaar.ir/app/ir.mobillet.app?l=fa'),
('Baran', 'https://cafebazaar.ir/app/com.gostaresh.mobilebank.boilerplate?l=fa'),
('Abanak', 'https://cafebazaar.ir/app/com.abankefarda?l=fa'),

('HamrahKart', 'https://cafebazaar.ir/app/com.adpdigital.mbs.ayande?l=fa'),
('HiBank', 'https://cafebazaar.ir/app/ir.karafarinbank.digital.mb?l=fa'),
('Banlet', 'https://cafebazaar.ir/app/com.ada.mbank.bankette?l=fa'),
('RefahMobileBank', 'https://cafebazaar.ir/app/com.refahbank.dpi.android?l=fa'),
('SepahHamrahBank', 'https://cafebazaar.ir/app/mob.banking.android.sepah?l=fa'),
('Resalt', 'https://cafebazaar.ir/app/mob.banking.android.resalat?l=fa'),
('Pasargad', 'https://cafebazaar.ir/app/mob.banking.android.pasargad?l=fa'),
('SaderatHamrahBank', 'https://cafebazaar.ir/app/com.isc.bsinew?l=fa'),
('TejaratHamrahBank', 'https://cafebazaar.ir/app/ir.tejaratbank.tata.mobile.android.tejarat?l=fa'),
('KeshavarziHamrahBank', 'https://cafebazaar.ir/app/com.bki.mobilebanking.android?l=fa'),
('PostBank', 'https://cafebazaar.ir/app/com.tosan.dara.postbank?l=fa'),
('Taavon', 'https://cafebazaar.ir/app/mob.banking.android.taavon?l=fa'),
('HamrahNovin', 'https://cafebazaar.ir/app/com.farazpardazan.enbank?l=fa'),
('Sarmayeh', 'https://cafebazaar.ir/app/ir.tes.sarmayeh?l=fa') 
;


END;