import re
import logging
# TODO: 3.3 compatiblity
import statistics as stats
from pathlib import Path
from ngcloud.report import SummaryStage, main as _main
from ngcloud.pipe import tuxedo
from ngcloud.util import open  # flake8: noqa

logger = logging.getLogger("external.%s" % __name__)

class TuxedoBaseStage(tuxedo.TuxedoBaseStage):
    template_find_paths = tuxedo.TuxedoBaseStage.template_find_paths[:]
    template_find_paths.insert(0, Path('templates'))

class TophatStage(TuxedoBaseStage, tuxedo.TophatStage):
    pass

class IndexStage(SummaryStage, TuxedoBaseStage, tuxedo.IndexStage):
    pass

class CufflinksStage(TuxedoBaseStage):
    """Cufflinks stage for Tuxedo pipeline"""
    result_foldername = 'cufflinks'
    template_entrances = 'cufflinks.html'

    def set_const(self):
        pass

    def parse(self):
        super().parse()
        self.set_const()
        for group, sample_list in self.sample_group.items():
            pass

class TuxedoReport(tuxedo.TuxedoReport):
    stage_classnames = [
        IndexStage, tuxedo.QCStage, TophatStage, CufflinksStage
    ]
    static_roots = tuxedo.TuxedoReport.static_roots[:]
    static_roots.extend([
        '../../template_dev/dev/shared',
        '../../template_dev/dev/tuxedo'
    ])

def main():
    argv = [
        "-p", "next_tuxedo.TuxedoReport",
        "../job_tuxedo_minimal",
        "-vv", "--color"
    ]
    _main(argv=argv)

if __name__ == '__main__':
    main()
