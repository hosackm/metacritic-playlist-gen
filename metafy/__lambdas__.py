from .__main__ import scrape, update_playlist


def spotify_lambda(e, ctx):
    print("Entered Spotify lambda handler")
    update_playlist()


def metacritic_lambda(e, ctx):
    print("Entered Metacritic lambda handler")
    scrape()
