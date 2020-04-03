from metafy.pitchfork import PitchforkSource


def test_pitchfork_source_supplies_6_albums(PitchforkReq):
    p = PitchforkSource()
    albums = p.gen_albums()

    num_albums = 6
    assert len(list(albums)) == num_albums
