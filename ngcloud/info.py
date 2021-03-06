from collections import OrderedDict
from pathlib import Path
import yaml
import ngcloud as ng
from ngcloud.util import open, _val_bool_or_none

logger = ng._create_logger(__name__)

class Sample:
    """Sample experiment run information.

    Parameters
    ----------
    name : string
    pair_end : {'R1', 'R2', False}, optional
    stranded : bool, optional

    Attributes
    ----------
    name : string
        Sample name. Pair-end samples should have same `name`
    full_name : string
        Auto-generated full sample name, containing pair-end info.

    Examples
    --------
    If a sample is pair-end, say sample 5566 has read 1 and 2, then one should
    explicitly creates two Sample instances

        >>> pe = [Sample(name='5566' % pe, pair_end=pe) for pe in ['R1', 'R2']]
        >>> pe
        [Sample(name='5566'), Sample(name='5566')]
        >>> print(pe[0])  # get first pair-end sample
        Sample 5566
            pair_end: R1
            stranded: None

        >>> pe[0].full_name
        '5566_R1'

   """

    _STR_FORMAT = '\n'.join([
        "Sample {0.name}",
        "    pair_end: {0.pair_end}",
        "    stranded: {0.stranded}"
    ])

    def __init__(self, name, pair_end=None, stranded=None):
        self.name = name            # SRR332241

        # bool check
        Sample._val_pair_end(pair_end)
        _val_bool_or_none(stranded, 'stranded')

        self.pair_end = pair_end
        self.stranded = stranded

        self.full_name = self._gen_full_name()
        logger.debug(
            "New sample(full_name: {0.full_name}) created".format(self)
        )

    def __repr__(self):
        return "Sample(name={0.name!r})".format(self)

    def __str__(self):
        return Sample._STR_FORMAT.format(self)

    def _gen_full_name(self):
        if self.pair_end:
            return "{0.name}_{0.pair_end}".format(self)
        else:
            return self.name

    @staticmethod
    def _val_pair_end(pair_end):
        if pair_end not in ['R1', 'R2', False, None]:
            raise ValueError(
                "Unexpected pair-end type: {}".format(pair_end)
            )


class JobInfo:
    """Store a job information.

    Attributes
    ----------
    id : str
    type : str
    root_path : Path
        path to result root
    sample_list : list
        Lists of :class:`Sample` in this job
    sample_group : OrderedDict
        Ordered mapping by grouping pair-end samples

    Parameters
    ----------
    root_path : path like object
    """

    def __init__(self, root_path):
        self.root_path = Path(root_path).resolve()
        logger.debug("Reading info from path: {!s}".format(self.root_path))

        self._raw = self._read_yaml()
        self.id = self._raw['job_id']
        self.type = self._raw['job_type']
        if 'pipe_param' not in self._raw:
            logger.warning('Pipeline parameters not found!')
            self.pipe_param = None
        else:
            self.pipe_param = self._raw.get('pipe_param', None)
        logger.debug(
            "JobInfo created (id: {0.id} type: {0.type})".format(self)
        )
        self.sample_list = self._parse_sample_list()
        self.sample_group = self._group_sample()

    def _read_yaml(self):
        logger.info("Reading job_info.yaml")
        with open(self.root_path / "job_info.yaml") as f:
            return yaml.load(f)

    def _parse_sample_list(self):
        logger.info("Get sample_list from YAML info")
        sample_list = []
        for sample in self._raw['sample_list']:
            name, info = next(iter(sample.items()))  # now a dict with one key
            # TODO: if user input SRR5566_R1 but no R2, needs to check
            sample_list.append(Sample(name, **info))
        return sample_list

    def _group_sample(self):
        sample_group = OrderedDict()
        for sample in self.sample_list:
            if sample.name in sample_group:
                sample_group[sample.name].append(sample)
            else:
                sample_group[sample.name] = [sample]
        return sample_group

