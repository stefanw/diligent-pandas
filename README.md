# pandas-diligent

`diligent` is a data proofing tool for pandas dataframes, best used in Jupyter notebooks.


Run `diligent` on your dataframes.

    from diligent import diligent

    diligent(df)

Run only certain kinds of checks.

        diligent(df, include='basic')

Run in verbose mode:

    diligent(df, verbose=True)

Register your own checks.

    from diligent import registry

    @registry.register(name='My custom check', tags='custom')
    def custom_check(series):
        yield 'Warning 1'
        yield 'Warning 2'
