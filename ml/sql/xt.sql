drop external table imagefiles;
create external table imagefiles
(
    dir text,
    basename text,
    size text,
    mode text,
    modtime text,
    isdir text,
    content_base64 text
) location ('xdrive://127.0.0.1:31416/images/**') 
format 'csv';

drop external table videofiles;
create external table videofiles
(
    dir text,
    basename text,
    size text,
    mode text,
    modtime text,
    isdir text,
    content_base64 text
) location ('xdrive://127.0.0.1:31416/videos/**')
format 'csv';

