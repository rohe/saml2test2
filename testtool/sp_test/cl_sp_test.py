#!/usr/bin/env python3
import logging

from aatest.session import SessionHandler

from saml2test.sp_test.tool import ClTester
from saml2test.sp_test.io import SamlClIO
from saml2test.sp_test.setup import setup

__author__ = 'roland'

logger = logging.getLogger("")


if __name__ == "__main__":
    test_id, kwargs, opargs = setup()

    sh = SessionHandler(session={}, **kwargs)
    sh.init_session({}, profile=kwargs['profile'])

    if test_id:
        if test_id not in kwargs['flows']:
            print(
                "The test id ({}) does not appear in the test definitions".format(
                    test_id))
            exit()

        io = SamlClIO(**kwargs)
        tester = ClTester(io, sh, **kwargs)
        if tester.run(test_id, **kwargs):
            io.debug_log(sh.session, test_id)
    else:
        for tid in sh.session["flow_names"]:
            # New fresh session handler for every test
            _sh = SessionHandler({}, **kwargs)
            _sh.init_session({}, profile=kwargs['profile'])
            io = SamlClIO(**kwargs)
            tester = ClTester(io, _sh, **kwargs)
            if tester.run(tid, **kwargs):
                if 'debug' in opargs and opargs['debug']:
                    io.debug_log(_sh.session, tid)
                else:
                    io.result(_sh.session)
            else:
                io.debug_log(_sh.session, tid)

            if 'dump' in opargs and opargs['dump']:
                io.dump_log(_sh.session, tid)
