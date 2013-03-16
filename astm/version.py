# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

__version_info__ = (0, 6, 0, 'dev', 0)
__version__ = '{version}{tag}{build}'.format(
    version='.'.join(map(str, __version_info__[:3])),
    tag='-' + __version_info__[3] if __version_info__[3] else '',
    build='.' + str(__version_info__[4]) if __version_info__[4] else ''
)
