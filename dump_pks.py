#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
from bluespider import mapped, game, mapdata

def main():
    description = (
        "Dumps maps to pks scripts. "
        "It will output everything to directory map_dump, "
        "or selected bank or map."
    )
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('rom', help='path to ROM image file')
    parser.add_argument('bank', nargs='?', default=None, type=int, help='bank_n')
    parser.add_argument('map', nargs='?', default=None, type= int, help='map_n')
    parser.add_argument('--stdout', action='store_true', default=False,
                        help='Output to stdout')
    parser.add_argument('--label', action='store_true', default=False,
                        help='Replace everything with @labels')
    parser.add_argument('--verbose', action='store_true', default=False,
                        help='List outputted files')
    args = parser.parse_args()

    if "rom" not in args:
        parser.print_help()
        return

    g = game.Game(args.rom)
    map_data = mapdata.MapData()
    if args.stdout:
        if args.bank is None or args.map is None:
            print("--stdout needs map and bank")
            return
        map_data.load(g, args.bank, args.map)
        print(mapped.export_script(g, map_data))
        return

    wdir = 'map_dump'
    os.makedirs(wdir, exist_ok=True)

    def vprint(*vargs, **kwargs):
        if args.verbose:
            print(*vargs, **kwargs)

    os.chdir(wdir)

    file_list = []

    fn = "banks.pks"
    vprint(fn)
    file_list.append(fn)
    with open(fn, "w") as f:
        f.write(mapped.export_banks_script(g, org=True, label=args.label))

    banks = g.banks
    if args.bank is not None:
        banks = [args.bank]

    for bank_n, _ in enumerate(banks):
        fn = "bank_{}.pks".format(bank_n)
        vprint(fn)
        file_list.append(fn)
        with open(fn, "w") as f:
            org = "@bank_{}".format(bank_n) if args.label else True
            f.write(mapped.export_maps_script(g, bank_n, org=org, label=args.label))

        bdir = str(bank_n)
        os.makedirs(bdir, exist_ok=True)
        map_ns = [i for (i, _) in enumerate(
            mapped.get_map_headers(g.rom_contents, bank_n, g.banks))]
        if args.map is not None:
            map_ns = [args.map]
        for map_n in map_ns:
            fn = os.path.join(bdir, "map_{}.pks".format(map_n))
            vprint(fn)
            try:
                map_data.load(g, bank_n, map_n)
            except:
                break
            file_list.append(fn)
            with open(fn, "w") as f:
                prefix = "@map_{}_{}_".format(bank_n, map_n)
                text = mapped.export_script(g, map_data, prefix, args.label)
                f.write(text)

    fn = "configs.pks"
    vprint(fn)
    file_list.append(fn)
    with open(fn, "w") as f:
        text = ("#define _TERMINATE_STRINGS\n"
                "#define _PRE_DYN_PADDING 0\n"
                "#define _POST_DYN_PADDING 0\n")
        f.write(text)

    fn = "include_list.pks"
    vprint(fn)
    with open(fn, "w") as f:
        text = "".join('#include "{}"\n'.format(fn) for fn in file_list)
        f.write(text)


if __name__ == "__main__":
    main()
