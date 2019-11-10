#!/usr/bin/python

import os
import sys

from os.path import join as path_join
from options import *
from os_utils import *


target_values = ['llvm64', 'llvmwin64']
mxe_targets = {'llvmwin64': {'arch': 'x86_64', 'mxe': 'mxe-Win64'}}


def make(opts: BaseOpts, target: str):
    stamp_file = path_join(opts.configure_dir, '.stamp-%s-make' % target)

    if os.path.isfile(stamp_file):
        return

    build_dir = path_join(opts.configure_dir, 'llvm-%s' % target)
    install_dir = path_join(opts.install_dir, 'llvm-%s' % target)

    mkdir_p(build_dir)
    mkdir_p(install_dir)

    CMAKE_ARGS = []

    if target in mxe_targets:
        mxe = mxe_targets[target]['mxe']
        arch = mxe_targets[target]['arch']

        CMAKE_ARGS += [
            '-DCMAKE_EXE_LINKER_FLAGS="-static"',
            '-DCROSS_TOOLCHAIN_FLAGS_NATIVE=-DCMAKE_TOOLCHAIN_FILE=%s/external/llvm/cmake/modules/NATIVE.cmake' % opts.mono_source_root,
            '-DCMAKE_TOOLCHAIN_FILE=%s/external/llvm/cmake/modules/%s.cmake' % (opts.mono_source_root, mxe),
            '-DLLVM_ENABLE_THREADS=Off',
            '-DLLVM_BUILD_EXECUTION_ENGINE=Off'
        ]

        if sys.platform == 'darwin':
            mingw_zlib_prefix = '%s/opt/mingw-zlib/usr' % opts.mxe_prefix
            if not os.path.isfile(mingw_zlib_prefix):
                mingw_zlib_prefix = opts.mxe_prefix

            CMAKE_ARGS += [
                '-DZLIB_ROOT=%s/%s-w64-mingw32' % (mingw_zlib_prefix, arch),
                '-DZLIB_LIBRARY=%s/%s-w64-mingw32/lib/libz.a' % (mingw_zlib_prefix, arch),
                '-DZLIB_INCLUDE_DIR=%s/%s-w64-mingw32/include' % (mingw_zlib_prefix, arch)
            ]

        replace_in_new_file(
            src_file='%s/sdks/builds/%s.cmake.in' % (opts.mono_source_root, mxe),
            search='@MXE_PATH@', replace=opts.mxe_prefix,
            dst_file='%s/external/llvm/cmake/modules/%s.cmake' % (opts.mono_source_root, mxe)
        )

    CMAKE_ARGS += [os.environ.get('llvm-%s_CMAKE_ARGS' % target, '')]

    make_args = [
	    '-C', '%s/llvm' % opts.mono_source_root,
        '-f', 'build.mk', 'install-llvm',
		'LLVM_BUILD=%s' % build_dir,
		'LLVM_PREFIX=%s' % install_dir,
		'LLVM_CMAKE_ARGS=%s' % ' '.join([a for a in CMAKE_ARGS if a])
    ]

    make_args += ['V=1'] if opts.verbose_make else []

    run_command('make', args=make_args, name='make')

    touch(stamp_file)


def clean(opts: BaseOpts, target: str):
    build_dir = path_join(opts.configure_dir, 'llvm-%s' % target)
    install_dir = path_join(opts.install_dir, 'llvm-%s' % target)
    stamp_file = path_join(opts.configure_dir, '.stamp-%s-make' % target)

    rm_rf(stamp_file)

    make_args = [
	    '-C', '%s/llvm' % opts.mono_source_root,
        '-f', 'build.mk', 'clean-llvm',
		'LLVM_BUILD=%s' % build_dir,
		'LLVM_PREFIX=%s' % install_dir
    ]

    make_args += ['V=1'] if opts.verbose_make else []

    run_command('make', args=make_args, name='make clean')


def main(raw_args):
    import cmd_utils

    parser = cmd_utils.build_arg_parser(description='Builds LLVM for Mono')

    default_help = 'default: %(default)s'

    parser.add_argument('action', choices=['make', 'clean'])
    parser.add_argument('--target', choices=target_values, action='append', required=True)

    cmd_utils.add_base_arguments(parser, default_help)

    args = parser.parse_args(raw_args)

    opts = base_opts_from_args(args)
    targets = args.target

    for target in targets:
        action = { 'make': make, 'clean': clean }[args.action]
        action(opts, target)


if __name__ == '__main__':
    from sys import argv
    main(argv[1:])
