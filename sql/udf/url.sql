-- if you have not created language plpythonu, do it.
--
-- create language plpythonu;
--

drop function if exists urlencode(text);
drop function if exists urldecode(text);

create function urlencode(t text) returns text
as $$
import urllib
return urllib.quote_plus(t)
$$ language plpythonu;

create function urldecode(t text) returns text
as $$
import urllib
return urllib.unquote_plus(t)
$$ language plpythonu;

