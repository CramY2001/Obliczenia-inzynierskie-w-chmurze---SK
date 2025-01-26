import numpy as np
from scipy.interpolate import RegularGridInterpolator
import json

def load_config(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)


# Funkcja do wczytania danych z pliku tekstowego

def load_table(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    header_1 = list(map(float, lines[0].split()))  # Pierwsza linia
    header_2 = list(map(float, lines[1].split()))  # Druga linia
    table = np.array([list(map(float, line.split())) for line in lines[2:]])  # Tabela
    return header_1, header_2, table


#  Funkcje do wpisywania danych z klawiatury w VScode

#def get_float_input(prompt, min_value, max_value):
#    while True:
#        try:
#            value = float(input(f"{prompt} (zakres: {min_value} - {max_value}): "))
#            if min_value <= value <= max_value:
#                return value
#            else:
#                print(f"Wartość musi być w zakresie od {min_value} do {max_value}.")
#        except ValueError:
#            print("Podaj liczbę!")

#def get_choice_input(prompt, choices):
#    while True:
#        try:
#            value = int(input(f"{prompt} (opcje: {', '.join(map(str, choices))}): "))
#            if value in choices:
#                return value
#            else:
#                print(f"Wybierz jedną z opcji: {', '.join(map(str, choices))}.")
#        except ValueError:
#            print("Podaj liczbę całkowitą z zakresu!")


#  Współczynnik kształtu ALPHA K

def alpha_values_load(prompt):
    
    while True:
        if prompt == 1:
            ro_d_values, D_d_values, alpha_k_values = load_table('./alpha_rozciaganie.txt')
            break
        elif prompt == 2:
            ro_d_values, D_d_values, alpha_k_values = load_table('./alpha_zginanie.txt')
            break
        elif prompt == 3:
            ro_d_values, D_d_values, alpha_k_values = load_table('./alpha_skrecanie.txt')
            break
        else:
            print("Wybierz jedną z opcji")
    fatigue_interpolator = RegularGridInterpolator((ro_d_values, D_d_values), alpha_k_values, bounds_error=False, fill_value=None)
    return fatigue_interpolator

# Funkcja obliczająca współczynnik kształtu
def Shape_factor(ro_d, D_d, fatigue_interpolator):
    point = np.array([ro_d, D_d])
    return fatigue_interpolator(point).item()


#  Współczynnik podatności na działanie karbu ETA

# Wczytywanie danych z plików
Zgo,stan_stali,eta_table = load_table('./notch.txt')

# Tworzenie interpolatorów
eta_interpolator = RegularGridInterpolator((Zgo,stan_stali), eta_table, bounds_error=False, fill_value=None)

# Funkcja obliczająca Współczynnik podatności na działanie karbu
def Notch_sens_factor(Zgo,stan_stali, eta_interpolator):
    point = np.array([Zgo,stan_stali])
    return eta_interpolator(point).item()


#  Współczynnik jakosci powierzchni BETA P

def beta_p_values_load(prompt):
    
    while True:
        if prompt == 1 or prompt == 2:
            Rm, typ_obrobki, beta_p_values = load_table('./beta_p.txt')
            break
        elif prompt == 3:
            Rm, typ_obrobki, beta_p_values = load_table('./beta_p_skrecanie.txt')
            break
        else:
            print("Wybierz jedną z opcji")
    beta_p_interpolator = RegularGridInterpolator((Rm, typ_obrobki), beta_p_values, bounds_error=False, fill_value=None)
    return beta_p_interpolator

# Funkcja obliczająca współczynnik jakosci powierzchni
def Surface_finish_factor(Rm, typ_obrobki, beta_p_interpolator):
    point = np.array([Rm, typ_obrobki])
    return beta_p_interpolator(point).item()


#Współczynnik wielkości przedmiotu GAMMA

# Wczytywanie danych z plików
Zgo_values, alpha_k_values, x_table = load_table('./x_table.txt')
d_values, x_values, gamma_table = load_table('./gamma_table.txt')

# Tworzenie interpolatorów
x_interpolator = RegularGridInterpolator((Zgo_values, alpha_k_values), x_table, bounds_error=False, fill_value=None)
gamma_interpolator = RegularGridInterpolator((np.log(d_values), x_values), gamma_table, bounds_error=False, fill_value=None)

# Funkcja obliczająca współczynnik wielkości przedmiotuu
def Size_factor(Zgo, alpha_k, d):
    x_value = x_interpolator([Zgo, alpha_k]).item()  # Interpolacja X
    return  gamma_interpolator([np.log(d), x_value]).item()  # Interpolacja gamma
   

#Wczytanie danych liczbowych z pliku json i obliczenie potrzebnych wartości
config = load_config("./config.json")
ro = config["ro"]
d = config["d"]
D = config["D"]
Re = config["Re"]
Rm = config["Rm"]
sigma_max = config["sigma_max"]
x = config["x"]
load_type = config["load_type"]
load_alternation_type = config["load_alternation_type"]
typ_obrobki = config["typ_obrobki"]
stan_stali = config["stan_stali"]
    
ro_d = ro/d
D_d = D/d
if load_type == 1:
    Zo = 0.5*Rm*0.7
    Zj = 0.5*Rm*1.3
elif load_type == 2:
    Zo = 0.5*Rm
    Zj = 0.5*Rm*1.7
elif load_type == 3:
    Zo = 0.5*Rm*0.6
    Zj = 0.5*Rm*1.2

if load_alternation_type == 1:
    sigma_a=sigma_max/2
    sigma_m=sigma_max/2
elif load_alternation_type == 2:
    sigma_a=sigma_max
    sigma_m=0
    
alpha_k = Shape_factor(ro_d, D_d,alpha_values_load(load_type))
eta = Notch_sens_factor(Zo,stan_stali,eta_interpolator)
beta_k = 1+eta*(alpha_k-1)
beta_p = Surface_finish_factor(Rm,typ_obrobki,beta_p_values_load(load_type))
beta = beta_k*beta_p
gamma= Size_factor(Zo, alpha_k, d)

safety_coeff = Zo/((beta*gamma*sigma_a)+sigma_m*((2*Zo/Zj)-1))

print(f"Aproksymowany współczynnik kształtu:                {alpha_k:.2f}")
print(f"Aproksymowany współczynnik jakości powierzchni:     {beta_p:.2f}")
print(f"Aproksymowany współczynnik wrażliwości na karb:     {eta:.2f}")
print(f"Aproksymowany współczynnik wielkości przedmiotu:    {gamma:.2f}\n")
print(f"Obliczony zmęczeniowy współczynnik bezpieczeństwa:  {safety_coeff:.2f}\n")