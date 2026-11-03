import subprocess
import os
import time
import psutil
import shutil
import random
import pandas as pand
import threading
import inspect
import copy
import ast
from datetime import date
from datetime import datetime
from dateutil.relativedelta import relativedelta


def set_specific_mt4_high_priority(target_path):
    target_path = target_path.lower()

    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in ['terminal.exe', 'terminal64.exe']:
                # Vérifie le chemin exact du processus
                if proc.info['exe'] and proc.info['exe'].lower() == target_path:
                    p = psutil.Process(proc.info['pid'])
                    p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                    print(f" Terminal ciblé (PID {proc.info['pid']}) → Priorité Below Normal")
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    print(" Terminal ciblé non trouvé")
    return False


def open_MT4 ( mt4, caches, file_parameter, opti_num, wait=True ):
    mt4_path = mt4

    print("Attend 20-30 secondes avant d'ouvrir MT4.")
    time.sleep(random.uniform(20, 30))
    process = subprocess.Popen([ mt4_path, file_parameter ])
    print("Attend 20-30 secondes APRèS OUVERTURE.")
    time.sleep(random.uniform(20, 30))

    print("MT4 lancé.\t\t", opti_num)

    if wait == True:
        set_specific_mt4_high_priority(mt4_path)

        process.wait()      # Attendre que MT4 se termine
        print("MT4 terminé.")
        delete_all_files_in_folder(caches)


def delete_all_files_in_folder( folder_path ):
    for fichier in os.listdir(folder_path):
        chemin = os.path.join(folder_path, fichier)

        if os.path.isfile(chemin):
            os.remove(chemin)

    print("Fichiers supprimés.")


def reduce_time(time, nb_month, nb_day):
    date_str = time

    d = datetime.strptime(date_str, "%Y.%m.%d")
    d = d - relativedelta(months=nb_month, days=nb_day)
    
    return d.strftime("%Y.%m.%d")


def secondes_entre_dates(date1):
    d1 = datetime.strptime(date1, "%Y.%m.%d")
    d2 = datetime.strptime('1970.01.01', "%Y.%m.%d")

    return str(abs(int((d1 - d2).total_seconds())))

def file_in_list(file_opti_base, info_opti_base, is_it_base_file, strip_or_no = True):
    with open(file_opti_base) as base:
        for line in base:
            line_modified = line.strip()
            if strip_or_no == False:
                line_modified = line

            if ( not (',' in line.strip()) ) and ( is_it_base_file == True ):
                info_opti_base.append([])

            if is_it_base_file == True :
                info_opti_base[-1].append(line_modified)
            
            else:
                info_opti_base.append(line_modified)


def file_in_list_initial_parameters(file_opti_base, info_opti_base, info_opti_base_copy):
    trading_asset              = "REAL"
    doc_py                     = r"\MT4_PY"
    path_absolute              = r"C:\Users"
    folder_in_users            = find_good_folder(path_absolute, "MT4_PY")
    folder_py_code             = path_absolute + folder_in_users + doc_py
    file_opti_base             = folder_py_code + file_opti_base
    folder_test                = path_absolute + folder_in_users + r"\AppData\Roaming\MetaQuotes\Terminal"
    num_folder_real, term_real = find_good_folder (folder_test, "", True, trading_asset) 
    original_path              = folder_test + num_folder_real + r"\MQL4\Files\parameters.txt"

    shutil.copy2(original_path, file_opti_base)
    
    comma       = ','
    colon       = ':'
    slash       = '/'
    bracket     = '[]'
    dash        = '-'
    sorted_list = []
    parameters  = []


    if os.path.exists(file_opti_base) == False:
        raise ValueError("Un fichier n'existe pas : ERROR --> ", file_opti_base)
    
    with open(file_opti_base) as base:
        for line in base:
            line_modified = line.strip()

            if ( "max_nb_opti_failed" == (line_modified.split("=")[0]) ) or ( "nb_asset_in_the_same_MT4" == (line_modified.split("=")[0]) ):
                parameters.append( int( line_modified.split("=")[1] ) )

            elif line_modified == slash:
                info_opti_base.append([])

            elif line_modified == dash:
                info_opti_base[-1].append([])
                comma_first = True

            elif (comma in line_modified):
                valu = (line_modified.split(comma)[0].strip(), line_modified.split(comma)[1].strip())

                if (colon in line_modified):
                    info_opti_base[-1][-1].append( [(float(valu[0]), valu[1])] )
                    verify_last_cell(info_opti_base_copy, info_opti_base)

                    info_opti_base[-1][-1].append(False)
                    verify_last_cell(info_opti_base_copy, info_opti_base, False)
                    info_opti_base[-1][-1].append(0)
                    verify_last_cell(info_opti_base_copy, info_opti_base, False)

                else:
                    info_opti_base[-1][-1].append( (int(valu[0]), int(valu[1])) )

            elif line_modified == bracket:
                info_opti_base[-1][-1].append([])
                verify_last_cell(info_opti_base_copy, info_opti_base)

                info_opti_base[-1][-1].append(False)
                verify_last_cell(info_opti_base_copy, info_opti_base, False)
                info_opti_base[-1][-1].append(0)
                verify_last_cell(info_opti_base_copy, info_opti_base, False)

            else:
                info_opti_base[-1][-1].append(line_modified)

    sorted_list = copy.deepcopy(info_opti_base)
    delete_all_cell(info_opti_base)

    sorted_in_alphabetical_order(info_opti_base, sorted_list)
    bot_already_launched_in_priority(info_opti_base)
    bad_asset_in_the_end(info_opti_base, parameters[1])
    info_opti_base.append([])
    info_opti_base[-1].append(parameters[0])
    info_opti_base[-1].append(parameters[1])

    if len(info_opti_base[-1]) != 2:
        raise ValueError("Où sont les paramètres ? : ", len(info_opti_base[-1]), "   ", info_opti_base[-1])




def verify_last_cell ( info_opti_base_copy, info_opti_base, is_it_dradown = True ):
    for h in range(len(info_opti_base_copy)):
        for b in range(len(info_opti_base_copy[h])):
            if info_opti_base_copy[h][b][0] == info_opti_base[-1][-1][0]:
                cell = (len(info_opti_base[-1][-1])-1)
                info_opti_base[-1][-1].pop()
                if is_it_dradown == True:
                    info_opti_base[-1][-1].append(copy.deepcopy(info_opti_base_copy[h][b][cell]))
                else:
                    info_opti_base[-1][-1].append(info_opti_base_copy[h][b][cell])


################################################################################
def bad_asset_in_the_end(sorted_list, parameters):
    for t in range(len(sorted_list)):
        temp_2 = []
        compte = 0
        taille = len(sorted_list[t])
        for h in range(len(sorted_list[t])):
            h -= compte
            if sorted_list[t][h][-1] < 0:
                temp = copy.deepcopy(sorted_list[t][h])
                sorted_list[t].pop(h)
                temp_2.append(copy.deepcopy(temp))
                compte +=1
        
        if ( compte > (taille-parameters) ):
            print("Trop d'actifs sont mauvais : remise à zéro --> ", compte, " > (", taille, "-", parameters,")")
            for n in range(len(temp_2)):
                temp_2[n][-1] = 0

        sorted_list[t] += copy.deepcopy(temp_2)


def bot_already_launched_in_priority(sorted_list):
    for t in range(len(sorted_list)):
        for h in range(len(sorted_list[t])):
            if len(sorted_list[t][h][-3]) >= 1:
                temp = copy.deepcopy(sorted_list[t][h])
                sorted_list[t].pop(h)
                sorted_list[t].insert(0, copy.deepcopy(temp))


def sorted_in_alphabetical_order(sorted_list, all_informations):
    for g in range(len(all_informations)):
        tab = copy.deepcopy(all_informations[g])
        y = sorted(tab, key=lambda x: x[0][0])
        sorted_list.append(y)
################################################################################


def fermer_mt4_par_chemin(path_str):
    try:
        # Commande PowerShell pour trouver et tuer le processus par chemin exact
        cmd = [
            "powershell",
            "-Command",
            f"Get-Process | Where-Object {{$_.Path -eq '{path_str}'}} | Stop-Process -Force"
        ]
        print(f"Attend 20-30 secondes, avant fermeture de MT4 ({path_str}).")
        time.sleep(random.uniform(20, 30))
        subprocess.run(cmd, check=True)
        print(f"MT4 ({path_str}) a été fermé avec succès. Attend 20-30 secondes")
        time.sleep(random.uniform(20, 30))
    except subprocess.CalledProcessError:
        print("Aucun processus MT4 trouvé à ce chemin.")
    except Exception as e:
        print(f"Erreur : {e}")
        sys.exit(1)


def mt4_est_ouvert(path_str):
    try:
        # Commande PowerShell pour vérifier si un processus avec ce chemin existe
        cmd = [
            "powershell",
            "-Command",
            f"(Get-Process | Where-Object {{$_.Path -eq '{path_str}'}}) -ne $null"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Nettoyage du résultat
        is_open = result.stdout.strip().lower() == "true"
        return is_open
    except subprocess.CalledProcessError:
        return False
    except Exception as e:
        print(f"Erreur : {e}")
        return False


def verify_line(line, name, asset_, find_symbol, bad_file):
    if line.split("=")[0].strip() == name and find_symbol == False:
        if line.split("=")[1].strip() != asset_:
            return ( True, True )

        else:
            return ( True, False )

    else:
        return ( find_symbol, bad_file )


def asset_is_launched(dossier_principal, asset_, time_period, one_asset_launched_at_least = False, prepare_profile_mode = False):
    value_                 = "0"
    name1                  = "symbol"
    name2                  = "period"
    name3                  = "HourStartTime"
    name4                  = "MinuteStartTime"
    name5                  = "HourStopTime"
    name6                  = "MinuteStopTime"
    one_chart_found        = False
    all_asset              = {}
    last_symbol            = ""

   # if one_asset_launched_at_least == True:
    #    print("MODE : one_asset_launched_at_least = True, find_symbol=", True)

    for dossier in os.listdir(dossier_principal):
        bad_file               = False
        asset_already_launched = False
        find_symbol            = False
        find_period            = False
        find_Hour_start        = False
        find_Hour_end          = False
        find_Min_start         = False
        find_Min_end           = False
        asset_found_profile    = False

        if one_asset_launched_at_least == True:
            find_symbol = True

        chemin_dossier = os.path.join(dossier_principal, dossier)

        if os.path.isfile(chemin_dossier) and ( os.path.splitext(chemin_dossier)[1] == ".chr" ):
            try:
                with open(chemin_dossier) as chem:
                    for line in chem:
                        if prepare_profile_mode == False:
                            find_symbol, bad_file = verify_line(line, name1, asset_, find_symbol, bad_file)
                            find_period, bad_file = verify_line(line, name2, time_period, find_period, bad_file)

                            find_Hour_start, asset_already_launched = verify_line(line, name3, value_, find_Hour_start, asset_already_launched)
                            find_Min_start, asset_already_launched  = verify_line(line, name4, value_, find_Min_start, asset_already_launched)
                            find_Hour_end, asset_already_launched   = verify_line(line, name5, value_, find_Hour_end, asset_already_launched)
                            find_Min_end, asset_already_launched    = verify_line(line, name6, value_, find_Min_end, asset_already_launched)

                            if bad_file == True or asset_already_launched == True:
                                break

                        else:
                            if line.split("=")[0].strip() == name1:
                                last_symbol = line.split("=")[1].strip()
                                if last_symbol in all_asset:
                                    all_asset[last_symbol][0].append(chemin_dossier)

                                else:
                                    all_asset[last_symbol] = [[chemin_dossier], ""]

                                asset_found_profile = True
                                break

            except PermissionError:
                continue

            if prepare_profile_mode == False:
                if asset_already_launched == True and find_symbol == True and find_period == True and bad_file == False:
                    print(asset_, " ou un autre actif a déjà été lancé.")
                    return ( True, chemin_dossier )

                elif bad_file == True and (find_symbol == True) and (find_Hour_start == find_Min_start == find_Hour_end == find_Min_end == False):
                    continue

                elif ( find_symbol == find_period == find_Hour_start == find_Min_start == find_Hour_end == find_Min_end == True ) and asset_already_launched == False:
                    print(asset_, " ou un autre actif N'a PAS été lancé.")
                    if one_asset_launched_at_least == False:
                        return ( False, chemin_dossier )

                    else:
                        one_chart_found = True
                        continue

                else:
                    raise ValueError(" Mauvaise Lecture du fichier .chr, ERROR :  find_symbol =", find_symbol, " find_period =", find_period, " bad_file =", bad_file, " asset_already_launched =", asset_already_launched, " find_Hour_start =", find_Hour_start, " find_Hour_end =", find_Hour_end, " find_Min_start =", find_Min_start, " find_Min_end =", find_Min_end)

            else:
                if (asset_found_profile == False) or (last_symbol == ""):   
                    raise ValueError(" Pas d'actif trouvé sur ce graphique, ERROR : ", last_symbol, "   ", asset_found_profile, "  ", chemin_dossier)


    if prepare_profile_mode == False:
        if one_asset_launched_at_least == True and one_chart_found == True:
            print("Pas d'actif actuellement.")
            return ( False, "" )

        raise ValueError(" Le fichier .chr du GRAPHIQUE n'a pas été trouvé. ERROR !!!!")

    else:
        if len(all_asset[last_symbol][0]) <= 1:
            del all_asset[last_symbol]
        else:
            all_asset[last_symbol][0].pop()

        return copy.deepcopy(all_asset)




def drawdown_is_exceeded(path_track, asset, max_drawdown):
    csv  = pand.read_csv(path_track, encoding="cp1252", sep=";")
    sume = 0
    max_ = 0

    for i in range(len(csv["Symbol"])):
        if ( csv["Symbol"][i] == asset ) and ( csv["Heure d'ouverture"][i] > max_drawdown[1] ):
            sume += float(csv["Profit en pourcentage"][i])
            if sume > max_:
                max_ = sume

            down = (-(max_ - sume))
            print("(-(",max_, "-", sume, ")) =", down, "  ", down < (-max_drawdown[0]), "   ", down, " < ", (-max_drawdown[0]), "  ", max_drawdown[0], "    ", max_drawdown[1])
            
            if down < (-max_drawdown[0]):
                return True

    return False

def drawdown_close_remove_list(track_record, asset, drawdown, set_real, path_mt4, two_combin, Mode_regulary_change = False):
    if os.path.exists(track_record) == True:
        if drawdown_is_exceeded(track_record, asset, drawdown[0]) == True:
            #if os.path.exists(set_real) == True:
               # fermer_mt4_par_chemin(path_mt4)
            #    os.remove(set_real)
            drawdown.pop(0)
            return True

            #else:
             #   raise ValueError(f"ERROR un fichier devrait exister : {set_real}")

        elif two_combin == True:
            if Mode_regulary_change == False:
                drawdown.pop()
            else:
                drawdown.pop(0)

    else:
        raise ValueError(f"ERROR un fichier n'existe pas : {track_record}")

    return False


def save_file_and_open_mt4(mt4, caches, set_real, file_set_input, file_opti):
    if os.path.exists(set_real) == False:
        shutil.copy(file_set_input, set_real)
        open_MT4(mt4, caches, file_opti, "REAL", False)
    else:
        raise ValueError(f"ERROR un fichier ne devrait pas exister : {set_real}")


def create_new_set(file_set_input, info_opti_base, info_new_value, info_var_optim, tab, exist, step_i, prepare_real):
    last_input = False
    input_diff = {"inp_risk_per_position", "HourStartTime", "HourStopTime"}

    with open(file_set_input, 'w') as set_inp:
        for u in range(len(info_opti_base)):
            for cmpt in range(len(info_opti_base[u])):
                if "Geo_Hour" == (info_opti_base[u][cmpt].split("=")[0]):
                    last_input = True

                if ( cmpt == 0 and prepare_real == True and last_input == True )  or ( (cmpt == 0) and ( (info_opti_base[u][cmpt].split("=")[0]) in input_diff ) and (step_i == 0) ):
                    set_inp.write(info_opti_base[u][cmpt]+'\n')
                    if step_i == 0:
                        print("First opti :", info_opti_base[u][cmpt])

                elif cmpt == 0 and exist:
                    set_inp.write(info_new_value[u]+'\n')

                elif cmpt == 1:
                    op_new = 0
                    if ( step_i < len(info_var_optim) ):
                        if ( (info_opti_base[u][cmpt].split(",")[0]) in info_var_optim[step_i] ):
                            op_new = 1
                            print("- ", info_opti_base[u][cmpt][:-1]+str(op_new))    ###########
                            tab.append(u)                                         ###########

                    set_inp.write(info_opti_base[u][cmpt][:-1]+str(op_new)+'\n')

                else:
                    set_inp.write(info_opti_base[u][cmpt]+'\n')


def find_good_folder (dossier_principal, under_folder, which_terminal = False, asset_ = ""):
    dossier_look_for  = ""

    for dossier in os.listdir(dossier_principal):
        chemin_dossier = os.path.join(dossier_principal, dossier)

        if os.path.isdir(chemin_dossier):
            if which_terminal == False:
                try:
                    for sous_dossier in os.listdir(chemin_dossier):
                        chemin_fichier = os.path.join(chemin_dossier, sous_dossier)

                        if os.path.isdir(chemin_fichier):
                            if (sous_dossier == under_folder):
                                dossier_look_for = chemin_dossier.split(dossier_principal)[-1]
                                print(sous_dossier, "   ", chemin_dossier, "  -->", dossier_look_for)
                                return dossier_look_for

                except PermissionError:
                    continue

            elif os.path.exists(chemin_dossier + r"\asset.txt") == True :
                with open(chemin_dossier + r"\asset.txt") as chem:
                    for line in chem:
                        if line.strip() == asset_: 
                            with open(chemin_dossier + r"\origin.txt", "r", encoding="utf-16") as origin:
                                for path_o in origin:
                                    dossier_look_for = ( chemin_dossier.split(dossier_principal)[-1], path_o.strip() )
                                    print(dossier_look_for[0], "----", dossier_look_for[1])
                                    return dossier_look_for

    if dossier_look_for == "":
        raise ValueError("Dossier introuvable  -->", dossier_principal, " ", under_folder, "  ",  which_terminal, " ", asset_)


def modify_text_file(path_file_start, lists, no_take_raw_file = True):
    info_file_start = []
    verify = 0

    print("Modifie ce fichier : ", path_file_start)

    file_in_list(path_file_start, info_file_start, False, no_take_raw_file)

    for cell in range(len(info_file_start)):
        for info_s in lists:
            if ( info_file_start[cell].split("=")[0] ) == info_s[0]:
                info_file_start[cell] = info_file_start[cell].split("=")[0] + "=" + info_s[1]
                verify += 1
                print(info_file_start[cell])

    if ( verify != len(lists) ):
        raise ValueError("N'a pas modifié les dates !!!!")

    if ( os.path.exists(path_file_start) ):
        os.remove(path_file_start)

    with open(path_file_start, 'w') as start_f:
        for z in range(len(info_file_start)):
            if z < (len(info_file_start)-1) and no_take_raw_file == True:
                info_file_start[z] = info_file_start[z]+'\n'

            start_f.write(info_file_start[z])


def modify_chart_profile(file_opti_base, path_file_start, zero_val = False):
    info_opti_base = []
    tab_name       = ["HourStartTime", "MinuteStartTime", "HourStopTime", "MinuteStopTime", "inp_real_refresh_rates"]
    count          = 0

    file_in_list(file_opti_base, info_opti_base, True, False)

    for i in range(len(info_opti_base)):
        while len(info_opti_base[i]) != 2:
            if len(info_opti_base[i]) < 2:
                info_opti_base[i].append("")
            else:
                info_opti_base[i].pop()

        info_opti_base[i][1] = info_opti_base[i][0].split("=")[-1]
        info_opti_base[i][0] = (info_opti_base[i][0].split("=")[0]).strip()

        if zero_val == True:
            for y in range(len(tab_name)):
                if info_opti_base[i][0] == tab_name[y]:
                    count += 1
                    info_opti_base[i][1] = "0\n"

                    if y >= (len(tab_name)-1):
                        info_opti_base[i][1] = "true\n"

    if count != len(tab_name) and zero_val == True:
        raise ValueError("All parameters aren't initialize to ZERO !!!!! But only -->", count, "!=", len(tab_name))

    modify_text_file(path_file_start, info_opti_base, False)


def prepare_files_before_optimisation(num_folder_real, is_it_testing, folder_py_code, folder_test, mql4, path_testing, pth_testing_files):
    shutil.copytree(folder_py_code + r"\Experts",              folder_test + num_folder_real + mql4 + r"\Experts",               dirs_exist_ok=True)
    shutil.copytree(folder_py_code + r"\files",                folder_test + num_folder_real + mql4 + r"\Files",                 dirs_exist_ok=True)
    shutil.copytree(folder_py_code + r"\files",                folder_test + num_folder_real + path_testing + pth_testing_files, dirs_exist_ok=True)
    shutil.copytree(folder_py_code + r"\TREND FOLLOWING ALGO", folder_test + num_folder_real + mql4 + r"\Include",               dirs_exist_ok=True)
    shutil.copytree(folder_py_code + r"\choice_combin",        folder_test + num_folder_real + path_testing,                     dirs_exist_ok=True)

    shutil.copytree(folder_py_code + r"\template",             folder_test + num_folder_real + r"\templates",                    dirs_exist_ok=True)
    shutil.copytree(folder_py_code + r"\script",               folder_test + num_folder_real + mql4 + r"\Scripts",               dirs_exist_ok=True)
    
    if ( is_it_testing == True ):
        shutil.copytree(folder_py_code + r"\start",      folder_test + num_folder_real, dirs_exist_ok=True)
    
    else:
        shutil.copytree(folder_py_code + r"\start_real", folder_test + num_folder_real, dirs_exist_ok=True)


def stop_tempo(demande_la_pause, pause, communication):
    if demande_la_pause.is_set():
        while communication.is_set():
            print("J'attend que ce soit finit pour l'autre MT4. ")
            time.sleep(random.uniform(5, 10))

        communication.set()

        print("Je donne l'autorisation de continuer. J'attend que la gestion du drawdown et des fichiers soit finit.")
        pause.set()

        while (demande_la_pause.is_set() == True) or (pause.is_set() == True):
            time.sleep(10)

        communication.clear()
        return True
    
    else:
        return False



def manage_real_mt4_during_night(test_asset, spread, copy_paste_files, backtest, forward_test, drawdown, max_nb_opti_failed, int_value_failed, opti_already_realized, close_and_open_mt4, asset_list_, call_first_info):
    trading_asset              = "REAL"
    doc_py                     = r"\MT4_PY"
    path_absolute              = r"C:\Users"
    folder_in_users            = find_good_folder(path_absolute, "MT4_PY")
    folder_py_code             = path_absolute + folder_in_users + doc_py
    folder_test                = path_absolute + folder_in_users + r"\AppData\Roaming\MetaQuotes\Terminal"
    num_folder, term_test      = find_good_folder (folder_test, "", True, test_asset)
    num_folder_real, term_real = find_good_folder (folder_test, "", True, trading_asset) 
    mql4                       = r"\MQL4"
    terminal_path_end          = r"\terminal.exe"
    path_testing               = r"\tester"
    pth_testing_files          = r"\files"
    pth_info_combin            = r"\Information_combinaison"

    MT4_PATH_test              = term_test + terminal_path_end
    MT4_PATH                   = term_real + terminal_path_end
    cache_folder               = folder_test + num_folder + path_testing + r"\caches"
    track_record               = folder_test + num_folder_real + mql4 + r"\Files\Track_record_trade_corrigé.csv"
    set_real                   = folder_test + num_folder_real + mql4 + r"\Presets\TREND FOLLOWING ALGO"+ test_asset + ".set"
    file_set_input             = folder_test + num_folder + path_testing + r'\TREND FOLLOWING ALGO'+ test_asset + '.set'
    file_set_real              = folder_test + num_folder + path_testing + r'\TREND FOLLOWING ALGO 2'+ test_asset + '.set'
    file_opti                  = "start.txt"
    file_opti_base             = folder_test + num_folder + path_testing + pth_testing_files + pth_info_combin + r'\optimisation_base.set'
    file_real_base             = folder_test + num_folder + path_testing + pth_testing_files + pth_info_combin + r'\optimisation_base 2.set'
    file_var_optim             = folder_test + num_folder + path_testing + pth_testing_files + pth_info_combin + r'\variable_to_optimize.txt'
    file_choice                = "choice_combin.txt"
    path_file_start            = folder_test + num_folder + r'\start.txt'
    path_file_start_real       = folder_test + num_folder_real + r'\start.txt'
    path_file_choice           = folder_test + num_folder + r'\choice_combin.txt'
    file_combinaison_conserved = folder_test + num_folder + path_testing + pth_testing_files + r'\combin_found'+ test_asset + '.txt'
    date_today   = ""
    begin    = ""
    end      = ""
    forward  = ""
    date_now = date.today().strftime("%Y.%m.%d")
    end        = date_now
    begin      = reduce_time(end, backtest[0], backtest[1])
    forward    = secondes_entre_dates(reduce_time(end, forward_test[0], forward_test[1]))
    date_today = date_now
    chart_path = ""
    launch_info = False
    profile_path        = folder_test + num_folder_real + r"\profiles"
    profile_multi_graph = profile_path + r"\Multi_graph"

    if close_and_open_mt4[0] == True:
        if mt4_est_ouvert(MT4_PATH):
            fermer_mt4_par_chemin(MT4_PATH)


        if ( os.path.exists(profile_multi_graph) and os.path.isdir(profile_multi_graph) ) == False:
            shutil.copytree(folder_py_code + r"\profile", profile_path, dirs_exist_ok=True)

        print("Profile Collé")
        current_chart = asset_is_launched(profile_multi_graph, test_asset, "5", False, True)
        asset_copied  = copy.deepcopy(asset_list_)
        print("Voici le dictionnaire AVANT: ", current_chart)
        for b in range(len(asset_copied)):
            if asset_copied[b] in current_chart:
                asset_list_.remove(asset_copied[b])
                del current_chart[asset_copied[b]]

        asset_copied  = copy.deepcopy(asset_list_)
        for z in range(len(asset_copied)):
            for cle in current_chart:
                if current_chart[cle][1] == "":
                    current_chart[cle][1] = asset_copied[z]
                    asset_list_.remove(asset_copied[z])
                    break

        if len(asset_list_) != 0:
            raise ValueError("Un actif n'a pas été placé !!!! ERROR : ", asset_list_)

        print("Voici le dictionnaire : ", current_chart)
        for clef in current_chart:
            if current_chart[clef][1] != "":
                for index in range(len(current_chart[clef][0])):
                    modify_text_file(current_chart[clef][0][index], [[ "symbol", (current_chart[clef][1]+"\n") ], [ "leftpos", "0\n" ]], False)


##################################################### 

    if copy_paste_files[0] == True:
        print("Documents collés TEST")
        prepare_files_before_optimisation(num_folder_real, False, folder_py_code, folder_test, mql4, path_testing, pth_testing_files)

    if copy_paste_files[1] == True:
        print("Documents collés REAL")
        prepare_files_before_optimisation(num_folder, True, folder_py_code, folder_test, mql4, path_testing, pth_testing_files)

#####################################################


    if opti_already_realized == True : #or ( (len(drawdown) >= 1) and (isinstance(drawdown[0], tuple)) and (call_first_info == True) ):
        for dra in range(len(drawdown)):
            if (isinstance(drawdown[dra], tuple) == False) and (isinstance(drawdown[dra], str) == False):
                if ( dra == 0 ):
                    drawdown[dra] = (drawdown[dra], datetime.now().strftime("%Y.%m.%d %H:%M:%S"))
                else:
                    drawdown[dra] = (drawdown[dra], drawdown[0][1])

                if isinstance(drawdown[dra], tuple) == False:
                    ValueError(f"Il devrait s'agir d'un tuple : {drawdown[dra]} dans {drawdown}")


        if ( len(drawdown) == 0 ) or (len(drawdown) == 1 and isinstance(drawdown[0], str) == True):
            int_value_failed[-1] += 1
            if ( int_value_failed[-1] >= max_nb_opti_failed ):
                int_value_failed[-1] = (-1)
                
            print("Rien --> Continuer Optimisation  + int_value_failed=", int_value_failed[-1])


        elif len(drawdown) == 1:
            print("Drawdown max : ", drawdown[0])
            date_conserved = drawdown[0][1]
            launch_info, chart_path = asset_is_launched(profile_multi_graph, test_asset, "5")
            if launch_info == True:
                int_value_failed[-1] += 1
                if ( int_value_failed[-1] >= max_nb_opti_failed ):
                    int_value_failed[-1] = (-1)

                if ( drawdown_close_remove_list(track_record, test_asset, drawdown, set_real, MT4_PATH, True, True) ==  True ):
                    int_value_failed[-1] = (-1)
                    modify_chart_profile(file_set_real, chart_path, True)
                    print("Drawdown dépassé ! Arrête l'EA : paramètres mis à 0, len --> ", len(drawdown), "  (normalement 0)  + int_value_failed=", int_value_failed[-1], "  (normalement -1)")
                else: 
                    drawdown.append(date_conserved)
                    modify_chart_profile(file_set_real, chart_path, True)
                    print("Drawdown OK ! Mais Arrête l'EA quand même : paramètres mis à 0.  len --> ", len(drawdown), "  (normalement 1)DATE  + int_value_failed=", int_value_failed[-1])

            else:
                int_value_failed[-1] = 0
                modify_chart_profile(file_set_real, chart_path)
            #  save_file_and_open_mt4(MT4_PATH, cache_folder, set_real, file_set_real, file_opti)
                print("Pas encore d'EA ! Enregistre les inputs dans 'Profiles', len --> ", len(drawdown), "  (normalement 1)  + int_value_failed=", int_value_failed[-1], "  (normalement 0)")


        elif len(drawdown) == 2:
            int_value_failed[-1] = 0
            print("Drawdown max : ", drawdown[0], "  et  ", drawdown[1])
            launch_info, chart_path = asset_is_launched(profile_multi_graph, test_asset, "5")
            if launch_info == True:
                if drawdown_close_remove_list(track_record, test_asset, drawdown, set_real, MT4_PATH, True, True) == True:
                    int_value_failed[-1] = (-1)
                    modify_chart_profile(file_set_real, chart_path)
                #  save_file_and_open_mt4(MT4_PATH, cache_folder, set_real, file_set_real, file_opti)
                    print("Drawdown dépassé ! Arrête l'EA : enregistre les inputs dans 'Profiles', len --> ", len(drawdown), "  (normalement 1)-->", drawdown[0], "   + int_value_failed=", int_value_failed[-1], "  (normalement -1)")
                else:
                    modify_chart_profile(file_set_real, chart_path)    # Mode_regulary_change = True ( change de combianaison dès que possible )
                    print("Drawdown OK ! Mais Arrête l'EA quand même : enregistre les inputs dans 'Profiles'. len --> ", len(drawdown), "  (normalement 1)-->", drawdown[0], "  + int_value_failed=", int_value_failed[-1], "  (normalement 0)")

            else:
                raise ValueError(f"Pas d'EA alors que len : {len(drawdown)}")


        else:
            raise ValueError(f"Liste drawdown ERROR, len : {len(drawdown)}")


        if int_value_failed[-1] == (-1):
            delete_all_cell(drawdown)



    if close_and_open_mt4[1] == True:
        if mt4_est_ouvert(MT4_PATH) == False:
            launch_info = asset_is_launched(profile_multi_graph, test_asset, "5", True)
            if launch_info[0] == True:
                open_MT4(MT4_PATH, cache_folder, file_opti, trading_asset, False)
            else:
                launch_info = asset_is_launched(profile_multi_graph, test_asset, "1", True)
                if launch_info[0] == True:
                    open_MT4(MT4_PATH, cache_folder, file_opti, trading_asset, False)

        else:
            raise ValueError("MT4 should be closed !!!!")

###########################################################################################################################################################

def verify_and_manage_real(all_informations, night, Event, signal, other_communication, num, first_call_var):
    doc_py           = r"\MT4_PY"
    path_absolute    = r"C:\Users"
    folder_in_users  = find_good_folder(path_absolute, "MT4_PY")
    folder_py_code   = path_absolute + folder_in_users + doc_py
    first_call = True
    date_today = ""

    while True:
        date_now = date.today().strftime("%Y.%m.%d")
        if other_communication.is_set():
            break

        if first_call == True or ( date_today != date_now and ( ( night[0] > night[1] and (datetime.now().hour >= night[0] or datetime.now().hour <= night[1]) ) or ( night[0] <= night[1] and (datetime.now().hour >= night[0] and datetime.now().hour <= night[1]) ) ) ):
            print("Demande de pause au programme principal")
            signal.set()
            print("En attente..")
            Event.wait()
            print("Reprise..")
            call_first_info = False

            if other_communication.is_set():
                break

            date_today = date_now

            if (first_call == True) and (first_call_var == True):
                call_first_info = True

            if first_call == True:
                first_call = False

            taille = all_informations[-1][1]
            if len(all_informations[num]) < taille:
                taille = len(all_informations[num])

            asset_list_ = [all_informations[fir][sec][0] for fir in range(len(all_informations)-1) for sec in range(taille)]

            for j in range(taille):
                close_open_mt4   = ( False, False )
                copy_paste_files = ( False, False )
                if j == 0:
                    copy_paste_files = ( True, True )
                    close_open_mt4   = ( True, close_open_mt4[1] )
                if ( j >= (taille-1) ):
                    close_open_mt4 = ( close_open_mt4[0], True )

                print("Manage drawdown        --> num =", num, "   j =", j, "   --> ", all_informations[num][j])
                manage_real_mt4_during_night(all_informations[num][j][0], all_informations[num][j][1], copy_paste_files, all_informations[num][j][2], all_informations[num][j][3], all_informations[num][j][4], all_informations[-1][0], all_informations[num][j], all_informations[num][j][-2], close_open_mt4, asset_list_, call_first_info)
                
                if all_informations[num][j][-2] == True:
                    all_informations[num][j][-2] = False

                print("Manage drawdown (AFTER) --> num =", num, "   j =", j, "   --> ", all_informations[num][j])


            if ( os.path.exists(folder_py_code+r"\all_informations.txt") ):
                os.remove(folder_py_code+r"\all_informations.txt")

            with open(folder_py_code+r"\all_informations.txt", "w", encoding="utf-8") as f:
                f.write(str(all_informations))


            print("C'est bon")
            signal.clear()
            Event.clear()

###########################################################################################################################################################

def manage_real_global(all_informations, list_event, other_communication):
    first_call_var = True
    cmpt_iteration = 0

    while True:
        if (other_communication.is_set() == False) and (len(list_event) == 0):
            for __ in range(len(all_informations)-1):
                list_event.append( ( threading.Event(), threading.Event() ) )

            if (first_call_var == True) and (cmpt_iteration == 1):
                first_call_var = False

            if cmpt_iteration == 0:
                cmpt_iteration += 1

            print("Lancement des thread --> verify_and_manage_real, --> first_call_var =", first_call_var)

            for g in range(len(all_informations)-1):
                thread = threading.Thread(target=verify_and_manage_real, args=(all_informations, (0, 23), list_event[g][0], list_event[g][1], other_communication, g, first_call_var,))
                thread.start()

###########################################################################################################################################################


def MT4_optimisation_function(test_asset, spread, backtest, forward_test, drawdown, pause, demande_la_pause, communication, count_bad):
    trading_asset              = "REAL"
    doc_py                     = r"\MT4_PY"
    path_absolute              = r"C:\Users"
    folder_in_users            = find_good_folder(path_absolute, "MT4_PY")
    folder_py_code             = path_absolute + folder_in_users + doc_py
    folder_test                = path_absolute + folder_in_users + r"\AppData\Roaming\MetaQuotes\Terminal"
    num_folder, term_test      = find_good_folder (folder_test, "", True, test_asset)
    num_folder_real, term_real = find_good_folder (folder_test, "", True, trading_asset) 
    mql4                       = r"\MQL4"
    terminal_path_end          = r"\terminal.exe"
    path_testing               = r"\tester"
    pth_testing_files          = r"\files"
    pth_info_combin            = r"\Information_combinaison"

    name_set_file              = 'TREND FOLLOWING ALGO'+ test_asset + '.set'
    MT4_PATH_test              = term_test + terminal_path_end
    MT4_PATH                   = term_real + terminal_path_end
    cache_folder               = folder_test + num_folder + path_testing + r"\caches"
    track_record               = folder_test + num_folder_real + mql4 + r"\Files\Track_record_trade_corrigé.csv"
    set_real                   = folder_test + num_folder_real + mql4 + r"\Presets\TREND FOLLOWING ALGO"+ test_asset + ".set"
    file_set_input             = folder_test + num_folder + path_testing + r'\TREND FOLLOWING ALGO'+ test_asset + '.set'
    file_set_real              = folder_test + num_folder + path_testing + r'\TREND FOLLOWING ALGO 2'+ test_asset + '.set'
    file_opti                  = "start.txt"
    file_script                = "download_data.txt"
    file_opti_base             = folder_test + num_folder + path_testing + pth_testing_files + pth_info_combin + r'\optimisation_base.set'
    file_real_base             = folder_test + num_folder + path_testing + pth_testing_files + pth_info_combin + r'\optimisation_base 2.set'
    file_var_optim             = folder_test + num_folder + path_testing + pth_testing_files + pth_info_combin + r'\variable_to_optimize.txt'
    file_choice                = "choice_combin.txt"
    path_file_start            = folder_test + num_folder + r'\start.txt'
    path_file_script           = folder_test + num_folder + r'\download_data.txt'
    path_file_start_real       = folder_test + num_folder_real + r'\start.txt'
    path_file_choice           = folder_test + num_folder + r'\choice_combin.txt'
    file_combinaison_conserved = folder_test + num_folder + path_testing + pth_testing_files + r'\combin_found'+ test_asset + '.txt'
    date_today   = ""
    begin    = ""
    end      = ""
    forward  = ""
    date_now = date.today().strftime("%Y.%m.%d")
    end        = date_now
    begin      = reduce_time(end, backtest[0], backtest[1])
    forward    = secondes_entre_dates(reduce_time(end, forward_test[0], forward_test[1]))
    date_today = date_now
    chart_path = ""
    launch_info = False
    result_got     = "NON"
    info_opti_base = []
    info_real_base = []
    info_var_optim = [set()]

    stop_tempo(demande_la_pause, pause, communication)

    if ( not os.path.exists(file_opti_base) ) or ( not os.path.exists(file_var_optim) ) :
        raise ValueError("!!!! 2 DOCUMENTS MANQUANTS !!!!")

###############################
    file_in_list(file_opti_base, info_opti_base, True)
    file_in_list(file_real_base, info_real_base, True)

    list_choice_start   = [["TestFromDate", begin], ["TestToDate", end], ["TestSymbol", test_asset], ["TestSpread", spread]]
    list_choice_start_1 = [["TestFromDate", begin], ["TestToDate", end], ["TestSymbol", test_asset], ["TestSpread", spread], ["TestExpertParameters", name_set_file]]
    list_script_start   = [["Symbol",  test_asset]]

    modify_text_file(path_file_start, list_choice_start_1)
    modify_text_file(path_file_choice, list_choice_start)

    modify_text_file(path_file_script, list_script_start)

###############################

    with open(file_var_optim) as optim:
        for line in optim:
            if ('-' in line.strip()):
                info_var_optim.append(set())

            else:
                info_var_optim[-1].add(line.strip())


    if len(info_opti_base[-2]) != 1:
        raise ValueError("File opti base MAUVAIS !!!")
    print("before : ", info_opti_base[-2][0])
    info_opti_base[-2][0] = info_opti_base[-2][0].split("=")[0]+"="+forward
    print("after : ", info_opti_base[-2][0])    


    tab = []        
    for step_i in range(len(info_var_optim)+1):
        info_new_value = []
        exist          = os.path.exists(file_combinaison_conserved)
        result_opti    = ""

        if exist:
            with open(file_combinaison_conserved) as new_val:
                for line in new_val:
                    if ( result_opti == "" ):
                        result_opti = line.strip()
                        result_got  = result_opti
                        print(result_opti)
                    else:
                        info_new_value.append(line.strip())

            if ( step_i < len(info_var_optim) ):
                os.remove(file_combinaison_conserved)

            print("before : ", info_new_value[-2])
            info_new_value[-2] = info_new_value[-2].split("=")[0]+"="+forward
            print("after : ", info_new_value[-2])

        elif step_i > 0:
            raise ValueError("!!!! COMBINAISON ERROR !!!!")

        
        if ( os.path.exists(file_set_input) ):
            os.remove(file_set_input)

        if step_i > 0:                    
            for h in tab:                 
                print("--> ", info_new_value[h])          
            tab = []                      

        create_new_set(file_set_input, info_opti_base, info_new_value, info_var_optim, tab, exist, step_i, False)


        if ( step_i < len(info_var_optim) ):
            if ( os.path.exists(folder_test + num_folder + path_testing + pth_testing_files + r"\optimisation resultbefore"+test_asset+" .csv") ):
                os.remove(folder_test + num_folder + path_testing + pth_testing_files + r"\optimisation resultbefore"+test_asset+" .csv")
                print("Suppression du fichier --> ", (folder_test + num_folder + path_testing + pth_testing_files + r"\optimisation resultbefore"+test_asset+" .csv"))

            if ( os.path.exists(folder_test + num_folder + path_testing + pth_testing_files + r"\optimisation result"+test_asset+" .csv") ):
                os.remove(folder_test + num_folder + path_testing + pth_testing_files + r"\optimisation result"+test_asset+" .csv")
                print("Suppression du fichier --> ", (folder_test + num_folder + path_testing + pth_testing_files + r"\optimisation result"+test_asset+" .csv"))


            print("Lance le Script.")
            open_MT4(MT4_PATH_test, cache_folder, file_script, step_i+1)

            open_MT4(MT4_PATH_test, cache_folder, file_opti, step_i+1)
            open_MT4(MT4_PATH_test, cache_folder, file_choice, step_i+1)

            if not os.path.exists(file_combinaison_conserved):
                raise ValueError("!!!! COMBINAISON ERROR !!!!")

        else:
            if ( os.path.exists(file_set_real) ):
                os.remove(file_set_real)

            create_new_set(file_set_real, info_real_base, info_new_value, info_var_optim, tab, exist, step_i, True)


    if (result_got != "NON") and (count_bad >= 0):
        if len(drawdown) == 1:
            if isinstance(drawdown[0], str) == True:
                temp = (float(result_got), drawdown[0])
                drawdown = temp

            else:
                drawdown.append(float(result_got))
        else:
            drawdown.append(float(result_got))


###########################################################################################################################################################


def launching_one_terminal_MT4(all_informations, list_event, communication, finish_event, num):
    verify_last_opti = False
    taille = all_informations[-1][1]
    if len(all_informations[num]) < taille:
        taille = len(all_informations[num])

    for n in range(taille):
        MT4_optimisation_function(all_informations[num][n][0], all_informations[num][n][1], all_informations[num][n][2], all_informations[num][n][3], all_informations[num][n][4], list_event[num][0], list_event[num][1], communication, all_informations[num][n][-1])

        all_informations[num][n][-2] = True

    while verify_last_opti == False:
        verify_last_opti = stop_tempo(list_event[num][1], list_event[num][0], communication)

    finish_event[num].set()


###########################################################################################################################################################

def delete_all_cell(tab):
    taille = range(len(tab))
    for q in taille:
        tab.pop()


def all_MT4_preparation(all_informations, list_event, communication, other_communication): 
    finish_event = []

    while True:
        while True:
            verif = True
            for cell in range(len(finish_event)):
                if finish_event[cell].is_set() == False:
                    verif = False 
                    break

            if verif == True:
                delete_all_cell(finish_event)
                break


        if other_communication.is_set() == False:
            other_communication.set()

        for cellul in range(len(list_event)):
            if list_event[cellul][1].is_set():
                list_event[cellul][0].set()

        info_opti_base_copy = copy.deepcopy(all_informations)
        if len(info_opti_base_copy) >= 1:
            info_opti_base_copy.pop()
        delete_all_cell(all_informations)


        file_in_list_initial_parameters(r"\parameters.txt", all_informations, info_opti_base_copy)

        for __ in range(len(all_informations)-1):
            finish_event.append( threading.Event() )

        delete_all_cell(list_event)
	
        print("all_informations remplit. Envoie le signal et attend 10 secondes.")
        for firs in range(len(all_informations)):
            for secon in range(len(all_informations[firs])):
                print(all_informations[firs][secon])
            print("")

        other_communication.clear()
        time.sleep(10)

        for u in range(len(all_informations)-1):
            thread_1 = threading.Thread(target=launching_one_terminal_MT4, args=(all_informations, list_event, communication, finish_event, u,))
            thread_1.start()
            
            time.sleep(10)

###########################################################################################################################################################

doc_py           = r"\MT4_PY"
path_absolute    = r"C:\Users"
folder_in_users  = find_good_folder(path_absolute, "MT4_PY")
folder_py_code   = path_absolute + folder_in_users + doc_py

list_event       = [( threading.Event(), threading.Event() )]
communication    = threading.Event()
other_communication = threading.Event()
other_communication.set()
all_informations = []

if ( os.path.exists(folder_py_code+r"\all_informations.txt") ):
    with open(folder_py_code+r"\all_informations.txt", "r", encoding="utf-8") as f:
        all_informations = ast.literal_eval(f.read().strip())

        if isinstance(all_informations, list) == False:
            raise ValueError("Ce n'est pas une liste !!!!! ", type(all_informations), "   ", all_informations)


thread = threading.Thread(target=manage_real_global, args=(all_informations, list_event, other_communication,))
thread.start()


all_MT4_preparation(all_informations, list_event, communication, other_communication)


