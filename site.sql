/*
The following table will be used to initialize a MySQL database.
BTW, I'm currently learning MySQL manual, so please advise ...
*/

drop database if exists ltok;

create database ltok;

use ltok;

-- grant permission
grant select, insert, update, delete on ltok.* to 'LTok'@'localhost' identified by 'LTok';

-- users table, `id` in Python `'%s%018d' % (uuid.uuid4().hex, int(time.time()*100000))`.
create table `users` (
    `id` varchar(50) not null,
    `name` varchar(50) not null,
    `email` varchar(50) not null,
    `password` varchar(50) not null,
    `admin` bool not null default 0,
    unique key `name` (`name`, `email`),
    primary key (`id`)
) engine=innodb default charset=utf8;

-- articles table. `created_at` in Python `int(time.time())`.
-- `content`: html format for display. `raw_content`: Markdown for update.
create table `articles` (
    `id` integer not null auto_increment,
    `title` varchar(255) not null,
    `content` mediumtext not null,
    `raw_content` mediumtext not null,
    `created_at` integer not null,
    `author` varchar(50) not null,
    `category` varchar(50) not null,
    key `created_at` (`created_at`),
    primary key (`id`)
) engine=innodb default charset=utf8;

-- tags table.
create table `tags` (
    `id` integer not null auto_increment,
    `tag_name` varchar(50) not null,
    unique key `tag_name` (`tag_name`),
    primary key (`id`)
) engine=innodb default charset=utf8;

-- relations of article and tags.
create table `article_tag` (
    `id` integer not null auto_increment,
    `article_id` integer not null,
    `tag_id` integer not null,
    key `relation` (`article_id`, `tag_id`),
    primary key (`id`)
) engine=innodb default charset=utf8;

-- comments table.
create table `comments` (
    `id` integer not null auto_increment,
    `article_id` integer not null,
    `username` varchar(50) not null,
    `content` mediutext not null,
    `created_at` integer not null,
    primary key (`id`)
) engine=innodb default charset=utf8;

-- insert admin to users.
insert into users(`id`, `name`, `password`, `email`, `admin`)
values('c60cdb9b918342faaa8f19be2f03ea63000141433017724118',
    'LTok', '05c98c6c62fa4865fdc5f8717ddfc2c0b1f83f57', 'dxc_wolf@163.com', 1);
