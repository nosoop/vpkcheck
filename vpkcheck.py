#!/usr/bin/python3

import vpk, os, json

GAME_PACKAGES = {
    'left4dead2': 'pak01_dir.vpk'
}

def safe_print(*objects, errors = 'ignore', **kwargs):
    '''
    I really don't want to have to bother with fixing up all my texts when printing, so here's
    an ascii-only print function
    '''
    print( *(str(t).encode('ascii', errors = errors).decode('ascii') for t in objects), **kwargs)

def main(args):
    original_pak = set()
    
    addon_info = {}
    
    # parse addon info
    if args.addon_list:
        with open(args.addon_list) as f:
            addon_info = json.load(f)
    
    with vpk.open(args.base_package) as pak01:
        original_pak = set(filter(lambda f: args.name_match in f, pak01))
    
    if not len(original_pak):
        raise AssertionError("base package is empty")
    
    addons = args.PACKAGE
    
    if args.mod_directory:
        workshop_dir = os.path.join(args.mod_directory, 'addons')
        for path, name, files in os.walk(workshop_dir):
            for file in files:
                _, ext = os.path.splitext(file)
                if ext == '.vpk':
                    addons.append(os.path.join(path, file))
    
    num_skipped = 0
    num_conflicting = 0
    for addon in addons:
        workshop_id, _ = os.path.splitext(os.path.basename(addon))
        addon_package = vpk.open(addon)
        
        file_desc = workshop_id
        
        if addon_info:
            file_info = addon_info.get('plugins').get(workshop_id)
            file_desc = '{id} ({name})'.format(id = workshop_id, name = file_info.get('title'))
        
        try:
            conflicting_items = original_pak & set(addon_package)
            
            if len(conflicting_items):
                safe_print('Conflicting files in', file_desc)
                safe_print(*('\t' + str(s) for s in conflicting_items), sep = '\n')
                
                print()
                num_conflicting += 1
        except BaseException as e:
            print('Skipping addon', file_desc, '({e.__class__.__name__}: {e})'.format(e = e))
            print()
            num_skipped += 1
    safe_print(len(addons),
            "plugin(s) checked ({} skipped, {} conflicts).".format(num_skipped, num_conflicting))

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
            description = "Displays info about potential / overlapping VPK file conflicts.",
            usage = "%(prog)s [options]", epilog = """Either a mod directory or a base package
            and checked packages must be specified.""")
    
    parser.add_argument('-m', '--mod-directory', metavar='DIR',
            help="path to the game's directory")
    parser.add_argument('-l', '--addon-list', metavar='FILE',
            help="path to addon list file (from workshop downloader); optional")
    parser.add_argument('-p', '--base-package', metavar='VPK',
            help="a Steam Workshop map collection to retrieve maps from")
    parser.add_argument('-n', '--name-match', metavar='STRING', default = '',
            help='Only check file paths containing the specified string')
    parser.add_argument('PACKAGE', nargs='*', help="one or more packages to check")
    
    args = parser.parse_args()
    
    if args.mod_directory and not args.base_package:
        # not great autodetection, but it'll do
        game_name = os.path.basename(args.mod_directory) or os.path.dirname(args.mod_directory)
        
        package = GAME_PACKAGES.get(game_name)
        
        if package:
            args.base_package = os.path.join(args.mod_directory, package)
        else:
            raise ValueError('No base package detected')
    
    if not args.mod_directory and not args.PACKAGE:
        raise ValueError("no addons/plugins specified and no addon directory detected")
    
    if not args.addon_list and args.mod_directory:
        addon_list = os.path.join(args.mod_directory, 'addons/workshop/addons.lst')
        if os.path.isfile(addon_list):
            print('Automatically detected addon list\n')
            args.addon_list = addon_list
    
    main(args)
