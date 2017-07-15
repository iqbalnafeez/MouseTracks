from __future__ import division
from multiprocessing import freeze_support
import time
import sys

from core.applications import RunningApplications, read_app_list
from core.compatibility import input
from core.config import CONFIG
from core.constants import DEFAULT_NAME
from core.files import list_data_files, format_name, load_program
from core.language import get_language
from core.maths import round_up
from core.messages import ticks_to_seconds, print_override
from core.misc import simple_bit_mask

STRINGS = get_language()
    
    
def user_generate():
    CONFIG.save()
    print_override(STRINGS['TYPE_PROFILE'].format(L=STRINGS['LIST']))
    profile = raw_input()

    if profile.lower() == STRINGS['LIST'].lower():
    
        #Read the data folder and format names
        all_files = list_data_files()
        if not all_files:
            print_override(STRINGS['DATA_FOLDER_EMPTY'])
            print_override(STRINGS['ENTER_TO_EXIT'])
            raw_input()
            sys.exit()
        programs = {format_name(DEFAULT_NAME): DEFAULT_NAME}
        for program_name in read_app_list().values():
            programs[format_name(program_name)] = program_name
        
        page = 1
        limit = 15
        maximum = len(all_files)
        total_pages = round_up(maximum / limit)
        change_sort = ['CURRENT_SORT_NAME', 2]

        #Ask for user input
        while True:
            offset = (page - 1) * limit

            results = all_files[offset:offset + limit]
            for i, r in enumerate(results):
                try:
                    program_name = programs[r]
                except KeyError:
                    program_name = r
                print_override('{}: {}'.format(i + offset + 1, program_name))
            print_override(STRINGS['CURRENT_PAGE'].format(C=page, T=total_pages, P=STRINGS['PAGE']))
            print_override(STRINGS[change_sort[0]].format(S='{} {}'.format(STRINGS['SORT'], change_sort[1])))
            print_override(STRINGS['HOW_TO_LOAD'])

            profile = raw_input()
            last_page = page
            
            #Change page
            if profile.lower().startswith('{P} '.format(P=STRINGS['PAGE'])):
                try:
                    page = int(profile.split()[1])
                    if not 0 < page <= total_pages:
                        raise ValueError
                except IndexError:
                    print_override(STRINGS['PAGE_INVALID'])
                except ValueError:
                    if page > total_pages:
                        page = total_pages
                    else:
                        page = 1
                        
            #Shortcut to change page
            elif profile.endswith('>'):
                if page < total_pages:
                    page += 1
            elif profile.startswith('<'):
                if page > 1:
                    page -= 1
            
            #Change sorting of profile list
            elif (profile.lower().startswith('{} '.format(STRINGS['SORT'])) 
                  or profile.lower() == STRINGS['SORT']):
                try:
                    sort_level = int(profile.split()[1])
                except ValueError:
                    sort_level = 0
                except IndexError:
                    sort_level = 1
                try:
                    sort_reverse = int(profile.split()[2])
                except (ValueError, IndexError):
                    sort_reverse = 0
                if sort_level == 1:
                    all_files = list_data_files()
                    change_sort = ['CURRENT_SORT_NAME', 2]
                elif sort_level == 2:
                    all_files = sorted(list_data_files())
                    change_sort = ['CURRENT_SORT_DATE', 1]
                if sort_reverse:
                    all_files = all_files[::-1]
            
            #Select profile
            else:
                try:
                    num = int(profile) - 1
                    if not 0 <= num <= maximum:
                        raise IndexError
                    profile_name = all_files[num]
                    try:
                        profile = programs[all_files[num]]
                    except KeyError:
                        profile = all_files[num]
                    break
                except ValueError:
                    break
                except IndexError:
                    print_override(STRINGS['PROFILE_NUMBER_INVALID'])

        try:
            profile = programs[profile]
        except KeyError:
            pass
    print_override(STRINGS['PROFILE_SELECTED'].format(P=profile))
    
    try:
        current_profile = format_name(RunningApplications().check()[0])
    except TypeError:
        pass
    else:
        selected_profile = format_name(profile)
        
        if current_profile == selected_profile:
            print_override(STRINGS['PROFILE_RUNNING_WARNING'])
            
            save_time = ticks_to_seconds(CONFIG['Save']['Frequency'], 1)
            metadata = load_program(profile, _metadata_only=True)
            if metadata['Modified'] is None:
                print_override(STRINGS['PROFILE_RUNNING_NOSAVE'])
                print_override(STRINGS['SAVE_FREQUENCY'].format(T=save_time))
                print_override(STRINGS['ENTER_TO_EXIT'])
                raw_input()
                sys.exit()
            else:
                last_save_time = time.time() - metadata['Modified']
                next_save_time = CONFIG['Save']['Frequency'] - last_save_time
                last_save = ticks_to_seconds(last_save_time, 1, allow_decimals=False)
                next_save = ticks_to_seconds(next_save_time, 1, allow_decimals=False)
                print_override(STRINGS['PROFILE_RUNNING_SAVE'].format(T=last_save))
                print_override(STRINGS['NEXT_SAVE_DUE'].format(T=next_save))


    generate_tracks = False
    generate_heatmap = False

    print_override(STRINGS['GENERATE_OPTIONS'])
    print_override(STRINGS['TYPE_OPTIONS'])
    print_override('1: {}'.format(STRINGS['TRACK_NAME']))
    print_override('2: {}'.format(STRINGS['CLICK_NAME']))
    print_override('3: {} (not working)'.format(STRINGS['KEY_NAME']))
    print_override('4: {} (not working)'.format(STRINGS['RAW_NAME']))

    result = simple_bit_mask(raw_input().split(), 2)

    if result[0]:
        generate_tracks = True
        
    if result[1]:
        
        generate_heatmap = True
        print_override('Which mouse buttons should be included in the heatmap?.')
        print_override(STRINGS['TYPE_OPTIONS'])
        print_override('1: {}'.format(STRINGS['MOUSE_BUTTON_LEFT']))
        print_override('2: {}'.format(STRINGS['MOUSE_BUTTON_MIDDLE']))
        print_override('3: {}'.format(STRINGS['MOUSE_BUTTON_RIGHT']))
        heatmap_buttons = simple_bit_mask(raw_input().split(), 3)
        CONFIG['GenerateHeatmap']['_MouseButtonLeft'] = heatmap_buttons[0]
        CONFIG['GenerateHeatmap']['_MouseButtonMiddle'] = heatmap_buttons[1]
        CONFIG['GenerateHeatmap']['_MouseButtonRight'] = heatmap_buttons[2]
        if not any(heatmap_buttons):
            generate_heatmap = False


    if generate_tracks or generate_heatmap:
        print_override(STRINGS['IMPORT_MODULES'])
        from core.image import RenderImage

        print_override(STRINGS['LOAD_PROFILE'].format(P=profile))
        r = RenderImage(profile)

        last_session_start = r.data['Ticks']['Session']['Total']
        last_session_end = r.data['Ticks']['Total']
        ups = CONFIG['Main']['UpdatesPerSecond']
        all_time = ticks_to_seconds(last_session_end, ups)
        last_session_time = ticks_to_seconds(last_session_end - last_session_start, ups)
        
        if not last_session_time or last_session_time == all_time:
            last_session = False
        
        else:
            while True:
                print_override(STRINGS['SESSION_OPTION'])
                print_override('1: {} [{}]'.format(STRINGS['SESSION_ALL'].format(T=all_time), STRINGS['DEFAULT']))
                print_override('2: {}'.format(STRINGS['SESSION_LAST'].format(T=last_session_time)))

                result = simple_bit_mask(raw_input().split(), 2, default_all=False)
                if result[0] and result[1]:
                    print_override(STRINGS['SELECT_ONE_OPTION'])
                elif result[1]:
                    last_session = True
                    break
                else:
                    last_session = False
                    break

        #Generate
        if generate_tracks:
            r.generate('Tracks', last_session)
        if generate_heatmap:
            r.generate('Clicks', last_session)
    else:
        print_override(STRINGS['NOTHING_CHOSEN'])

        
if __name__ == '__main__':
    freeze_support()
    user_generate()
