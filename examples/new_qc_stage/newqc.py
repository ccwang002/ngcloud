import logging
from pathlib import Path
from collections import OrderedDict, namedtuple
from ngcloud.report import Report, main as _main
from ngcloud.pipe import (
    get_shared_static_root
)
from ngcloud.pipe.tuxedo import QCStage
from ngcloud.util import open

logger = logging.getLogger("external.%s" % __name__)

OverSeq = namedtuple(
    "OverSeq", ["seq", "count", "percentage", "possible_source"])

class NewQCStage(QCStage):
    template_find_paths = QCStage.template_find_paths[:]
    template_find_paths.insert(
        0, Path('report', 'templates')
    )
    template_entrances = 'newqc.html'
    embed_result_joint = []
    embed_result_persample = [
        {'src': '.',
         'patterns': ['Images/*.png'],
         'dest': 'qc_sample/pics'},
    ]

    FASTQC_FILENAME = {
        'Per base sequence quality': 'per_base_quality.png',
        'Per sequence quality scores': 'per_sequence_quality.png',
        'Per base sequence content': 'per_base_sequence_content.png',
        'Per base GC content': 'per_base_gc_content.png',
        'Per sequence GC content': 'per_sequence_gc_content.png',
        'Per base N content': 'per_base_n_content.png',
        'Sequence Length Distribution': 'sequence_length_distribution.png',
        'Sequence Duplication Levels': 'duplication_levels.png',
    }
    FASTQC_NOFILE = [
        'Basic Statistics',
        'Overrepresented sequences',
        'Kmer Content'
    ]
    FASTQC_GLYPH = {
        'pass': 'glyphicon-ok',
        'warn': 'glyphicon-exclamation-sign',
        'fail': 'glyphicon-remove'
    }

    def read_fastqc_data(self, sample):
        qc_info = OrderedDict()
        over_seq = []
        qc_desc = None
        qc_data_pth = self.result_root / sample.full_name / 'fastqc_data.txt'
        with open(qc_data_pth) as qc_data:
            # parse FASTQC by brute force
            for line in qc_data:
                new_sec = line.startswith('>>')
                sec_end = line.startswith('>>END_MODULE')
                if new_sec and not sec_end:
                    qc_desc, qc_status = line.rstrip()[2:].rsplit('\t', 1)
                    qc_info[qc_desc] = qc_status
                    if qc_desc == "Overrepresented sequences":
                        next_line = next(qc_data)
                        while not sec_end:
                            if not next_line.startswith("#Seq"):
                                over_seq.append(
                                    OverSeq(*next_line.rstrip().split('\t'))
                                )
                            next_line = next(qc_data)
                            sec_end = next_line.startswith('>>END_MODULE')
        logger.debug(
            "Sample {}'s qc_info: {}".format(sample.full_name, qc_info)
        )
        logger.debug("Over_seq length: {}".format(len(over_seq)))
        return qc_info, over_seq

    def parse(self):
        self.result_info['qc_info'] = dict()
        self.result_info['over_seq'] = dict()
        for sample in self.job_info.sample_list:
            qc_info, over_seq = self.read_fastqc_data(sample)
            self.result_info['qc_info'][sample.full_name] = qc_info
            self.result_info['over_seq'][sample.full_name] = over_seq
        self.result_info['stage_mapping'] = [
            ('qc', 'newqc.html', 'Quality Control')
        ]
        self.result_info.update({
            "FASTQC_FILENAME": self.FASTQC_FILENAME,
            "FASTQC_NOFILE": self.FASTQC_NOFILE,
            "FASTQC_GLYPH": self.FASTQC_GLYPH
        })


class QCOnly(Report):
    def __init__(self):
        logger.warning("Custom message")
        super(Report, self).__init__()
    stage_classnames = [NewQCStage]
    static_roots = [
        get_shared_static_root(),
        '../../template_dev/public',
    ]

def main():
    argv = [
        "-p", "newqc.QCOnly", "job_new_qc",
        "-vv", "--color"
    ]
    _main(argv=argv)

if __name__ == '__main__':
    main()
