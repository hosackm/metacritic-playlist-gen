# metacritic-playlist-gen
Metacritic Playlist Generator is a program that will create a Spotify playlist of albums that were highly rated on Metacritic.  To read about the inspiration or how this project works go to [my blog post about it](http://matthosack.com/post/intro_to_apis/web_api_intro)

## To use this script
You must set the following environment variables before running the script.

    * MPGEN_CLIENT_ID (your spotify client id)
    * MPGEN_CLIENT_SECRET (your spotify client secret
    * MPGEN_AUTH_TK (your spotify authentication token)
    * MPGEN_REF_TK (your spotify refresh token)

If you don't have these environment variables set correctly or you're not authorized to access the user's playlist that you specify things won't work.
