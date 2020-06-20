def test_import():
    import backup_to_cloud.__main__ as execute

    assert vars(execute)["__name__"] == "backup_to_cloud.__main__"
