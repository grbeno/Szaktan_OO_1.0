import pandas as pd
import numpy as np
import szaktanData as mydata
from openpyxl.workbook import Workbook

class SzaktanClass():

    def __init__(self, labor,techn,fajlagos,nmax,megosztas):
        
        " Input adatok <- csv táblák "
        self.labor = self.__readCsv(labor)
        self.mintaszam = []
        self.labor_A = self.__groupBy(self.labor,'PARCELLA') # 'col' <- aggr.
        self.labor_A_rows = self.labor_A.shape[0]
        self.techn = self.__readCsv(techn)
        
        " Adatok számításokhoz "
        self.fajlagos_T = self.__readCsv(fajlagos)
        self.nmax_T = self.__readCsv(nmax) 
        self.megosztas_T = self.__readCsv(megosztas)
        
        " Tömbök -> eredményközlés "
        self.tabla, self.N_min, self.P_min, self.K_min, self.Mg_min, self.Zn_min, self.Mn_min, self.Cu_min, \
        self.N_ftig, self.P_ftig, self.K_ftig, self.N_btig, self.P_btig, self.K_btig, self.N_ntig, self.P_ntig, self.K_ntig, \
        self.Nmax_min, self.Nmax_eredmeny = ([] for i in range(19))
        self.megosztas = [[] for i in range(self.labor_A_rows)] # <- 5 elemes adatsorokhoz
       
        " Feldolgozás "
        self.eredmenyek()
        
        " Excel output "
        self.resInDataframe().to_excel("eredmenyek.xlsx",sheet_name='Szaktan')
        

    " ADATKEZELŐ FÜGGVÉNYEK "

    def __readCsv(self, csvfile):
        " csv fájlt beolvas ... "
        df = pd.read_csv(csvfile, sep=';', decimal=',', escapechar='<', encoding="iso-8859-2")
        df = df.drop_duplicates() # <- ismétlődő sorok törlése
        df = df.fillna(0) # 0 <- nan 
        return df

    def __groupBy(self, df,by):
        " Kiválasztott oszlopok/labor paraméterek(számok) átlaga 'groupby' id alapján "
        self.mintaszam =list(df.groupby(by).size().values) # mintaszámok
        df = df.groupby(by, as_index=False, sort=False).mean()
        df['KA'] = df['KA'].apply(np.ceil).astype(int) # felfele kerekített
        return df.round(2)

    def resInDataframe(self):
        " 1. Eredmények dictionary-be foglalása 2. Visszatértés pandas DataFrame-ben " # 
        d = {'ID': self.tabla,'N_min': self.N_min, 'P_min': self.P_min, 'K_min': self.K_min, 'Mg_min': self.Mg_min, 'Zn_min': self.Zn_min, 'Mn_min': self.Mn_min,
            'Cu_min': self.Cu_min, 'N_ftig': self.N_ftig, 'P_ftig': self.P_ftig, 'K_ftig': self.K_ftig, 'N_btig': self.N_btig, 'P_btig': self.P_btig,
            'K_btig': self.K_btig, 'N_ntig': self.N_ntig, 'P_ntig': self.P_ntig, 'K_ntig': self.K_ntig, 'Nmax_min': self.Nmax_min, 'Nmax_eredmeny': self.Nmax_eredmeny, 'Mintaszam': self.mintaszam, 'Megosztas': self.megosztas}
        df = pd.DataFrame(data=d)
        return df
    
    
    # Tesztelés:
    def teszt(self):
        return self.labor_A #.dtypes
         
    
    " ADATFELDOLGOZÁS -> EREDMÉNYKÖZLÉS "

    def eredmenyek(self):
        " Minősítések, tápanyagigények 1D, megosztás 2D tömbbe rendezve "
        for row in range(self.labor_A_rows): # megfelel a 'labor_A' tábla indexelésének!
           
            " MINŐSíTÉSEK "
            
            " Minősítés <- makroelemek (N,P,K)"
            
            # Nitrogén
            self.N_min.append(self.__minosit_makro(np.array(mydata.nitrogen), 
                self.labor_A['KA'].iloc[row], self.labor_A['HUMUSZ'].iloc[row], 
                self.techn['THK'].iloc[row], mydata.nk_intv, mydata.minositesek))
            # P2o5
            self.P_min.append(self.__minosit_makro(np.array(mydata.foszfor), 
                self.labor_A['MESZ'].iloc[row], self.labor_A['P2O5'].iloc[row], 
                self.techn['THK'].iloc[row], mydata.p_intv, mydata.minositesek))
            # K2o
            self.K_min.append(self.__minosit_makro(np.array(mydata.kalium), 
                self.labor_A['KA'].iloc[row], self.labor_A['K2O'].iloc[row], 
                self.techn['THK'].iloc[row], mydata.nk_intv, mydata.minositesek))
            
            " Minősítés <- mikroelemek (Mg,Zn,Mn,Cu) "
            
            # Mg
            self.Mg_min.append(self.__minosit_mikro_1(np.array(mydata.magnezium), 
                self.labor_A['KA'].iloc[row], self.labor_A['MG'].iloc[row], 
                mydata.mg_cu_intv, mydata.minositesek[1:4]))
            # Zn
            self.Zn_min.append(self.__minosit_mikro_1(np.array(mydata.cink), 
                self.labor_A['KA'].iloc[row], self.labor_A['ZN'].iloc[row], 
                mydata.zn_mn_intv, mydata.minositesek[1:4:2]))
            # Mn
            self.Mn_min.append(self.__minosit_mikro_2(np.array(mydata.mangan), 
               self.labor_A['KA'].iloc[row], self.labor_A['MN'].iloc[row], self.labor_A['PH_KCL'].iloc[row], 
               mydata.zn_mn_intv, mydata.mangan_col))
            # Cu
            self.Cu_min.append(self.__minosit_mikro_2(np.array(mydata.rez), 
                self.labor_A['KA'].iloc[row], self.labor_A['CU'].iloc[row], self.labor_A['HUMUSZ'].iloc[row], 
                mydata.mg_cu_intv, mydata.rez_col))
            
            " TÁPANYAGIGÉNYEK - FAJLAGOS, BRUTTÓ, NETTÓ " 
            
            " Nitrogén "

            # N fajlagos
            self.N_ftig.append(self.__ftig(self.techn['TNOV_NEV'].iloc[row], 
                self.techn['THK'].iloc[row], 'Nitrogen', self.N_min[row]))
            # N bruttó
            self.N_btig.append((self.N_ftig[row]*self.techn['TNOV_TERM'].iloc[row]*10).round(2))
            # N nettó (bruttó-korrekció)
            self.N_ntig.append( self.N_btig[row] - (
                self.techn['ELV_PILL'].iloc[row] +
                self.techn['ELV_EVPILL'].iloc[row] +
                self.techn['ELV_LUC2EV'].iloc[row] +
                self.techn['ELV_KUKNR_N'].iloc[row] +
                self.techn['KAR_N'].iloc[row] * self.techn['KAR_SZ'].iloc[row]/100 -
                self.techn['PENT_N'].iloc[row] + self.techn['IST_M'].iloc[row] * self.techn['IST_N1'].iloc[row]/10 +
                self.techn['IST_N2'].iloc[row] * self.techn['IST_M'].iloc[row]/10)
            )
            # Ne legyen negatív:
            if self.N_ntig[row] < 0:
                self.N_ntig[row] = 0

            " Foszfor "

            # P fajlagos
            self.P_ftig.append(self.__ftig(self.techn['TNOV_NEV'].iloc[row], 
                self.techn['THK'].iloc[row], 'Foszfor', self.P_min[row]))
            # P bruttó
            self.P_btig.append((self.P_ftig[row]*self.techn['TNOV_TERM'].iloc[row]*10).round(2))
            # P nettó (bruttó-korrekció)
            self.P_ntig.append( self.P_btig[row] - (
                self.techn['IST_P1'].iloc[row] * self.techn['IST_M'].iloc[row]/10 +
                self.techn['IST_P2'].iloc[row]/10 * self.techn['IST_M'].iloc[row] +
                self.techn['KAR_P'].iloc[row] * self.techn['KAR_SZ'].iloc[row]/100)
            )
            # Ne legyen negatív:
            if self.P_ntig[row] < 0:
                self.P_ntig[row] = 0

            " Kálium "

            # K fajlagos
            self.K_ftig.append(self.__ftig(self.techn['TNOV_NEV'].iloc[row], 
                self.techn['THK'].iloc[row], 'Kalium', self.K_min[row]))
            # K bruttó
            self.K_btig.append((self.K_ftig[row]*self.techn['TNOV_TERM'].iloc[row]*10).round(2))
            # K nettó (bruttó-korrekció)
            self.K_ntig.append( self.K_btig[row] - (
                self.techn['ELV_KUKN_K'].iloc[row] +
                self.techn['SZ_KUK'].iloc[row] * self.techn['SZ_KUK_T'].iloc[row] +
                self.techn['SZ_NPF'].iloc[row] * self.techn['SZ_NPF_T'].iloc[row] +
                self.techn['SZ_GAB'].iloc[row] * self.techn['SZ_GAB_T'].iloc[row] +
                self.techn['KAR_K'].iloc[row] * self.techn['KAR_SZ'].iloc[row]/100 +
                self.techn['IST_M'].iloc[row] *  self.techn['IST_K1'].iloc[row]/10 +
                self.techn['IST_M'].iloc[row] *  self.techn['IST_K2'].iloc[row]/10)
            )
            # Ne legyen negatív:
            if self.K_ntig[row] < 0:
                self.K_ntig[row] = 0


            "NITROGÉN HATÓANYAG MAXIMUMAI"
            
            # Nmax minősítés
            self.Nmax_min.append(self.__minosit_makro(np.array(mydata.nmax), 
                self.labor_A['KA'].iloc[row], self.labor_A['HUMUSZ'].iloc[row], 
                self.techn['THK'].iloc[row], mydata.nmax_intv, mydata.minositesek[1:4]))
            # Nmax értékek
            self.Nmax_eredmeny.append(self.__nmax(self.techn['TNOV_NEV'].iloc[row], self.techn['THK'].iloc[row], self.Nmax_min[row]))

            " MEGOSZTÁS ADATSOROK "

            self.megosztas[row].append(self.__megosztas(self.labor_A['KA'].iloc[row], self.techn['TNOV_NEV'].iloc[row], self.techn['THK'].iloc[row], mydata.megosztas))

            # Tábla -> Id
            self.tabla.append(self.labor_A['PARCELLA'].iloc[row])


    " ADATOK MEGOSZTÁS TÁBLÁZATOKHOZ "

    def __megosztas(self, ka,tnov,thk,KA_tabla): 
        " A Megosztas_T táblából a megosztás adatsorral tér vissza, ahol a többi oszlop == ..."
        ka_dim = self.__is_in_intv(ka,KA_tabla[thk-1]) # -1 -> index
        df = self.megosztas_T.loc [ 
            (self.megosztas_T['NOV'] == tnov) & 
            (self.megosztas_T['THK'] == thk) &
            (self.megosztas_T['KA_DIM'] == ka_dim)
            ]
        try: 
            result = df["MEGOSZTAS"].values
        except IndexError: # ha nincs eredmény
            return '-'
        else:
            return result

    " NITRÁT MAXIMUOK MEGHATÁROZÁSA "
    
    def __nmax(self, tnov,thk,minosites): 
        " A nmax_T táblából az nmax értékkel tér vissza, ahol a többi oszlop == ..."
        df = self.nmax_T.loc [
            (self.nmax_T['NOV'] == tnov) & 
            (self.nmax_T['THK'] == thk) & 
            (self.nmax_T['MINOSITES'] == minosites)
            ]
        try:
            result = df["NMAX"].iloc[0]
        except IndexError:
            return '-'
        else:
            return result


    " NÖVÉNYEK FAJLAGOS TÁPANYAGIGÉNYE "

    def __ftig(self, tnov,thk,elem,minosites): 
        " A fajlagos_T táblából a fajlagos értékkel tér vissza, ahol a többi oszlop==..."
        df = self.fajlagos_T.loc [
            (self.fajlagos_T['NOV'] == tnov) & 
            (self.fajlagos_T['MAKROELEM'] == elem) & 
            (self.fajlagos_T['THK'] == thk) & 
            (self.fajlagos_T['MINOSITES'] == minosites)
            ]
        try:
            result = df["FAJLAGOS"].iloc[0]
        except IndexError:
            return 0
        else:
            return result

    
    " FÜGGVÉNYEK MINŐSíTÉSEKHEZ "

    def __minosit_makro(self, arr,p1,p2,thk,intv,minositesek):
        " NPK, Nmax minősítése ... p1=KA/MESZ,p2=H%/P2o5/K2o, "
        pos = (thk-1, self.__is_in_intv(p1,intv[thk-1]))
        # Minősítés:
        i = self.__is_in_intv(p2,arr[pos]) # pos <-(i,j)
        if i is not None:
            return minositesek[i] # 6/3 fokozatú
        return "<MINOSIT_hiba!>" 


    def __minosit_mikro_1(self, arr,p1,p2,intv,minositesek):
        " Magnézium és Cink minősítése ... p1=KA,p2=Mg/Zn "
        pos = self.__is_in_intv(p1,intv)
        # Minősítés:
        i = self.__is_in_intv(p2,arr[pos]) 
        if i is not None:
            return minositesek[i]
        return "<MINOSIT_hiba!>"


    def __minosit_mikro_2(self, arr,p1,p2,p3,intv1,intv2):
        " Mangán és Réz minősítése ... p1=KA,p2=Mn/Cu,p3=ph/H%"
        i = self.__is_in_intv(p1,intv1)
        j = self.__is_in_intv(p3,intv2)
        res = self.__is_in_intv(p2,list([arr[i,j]])) # list[]-> 1D-re!
        if res is not None:
            return "nem megfelelő"
        else: 
            return "megfelelő"
        
        
    def __is_in_intv(self, number,intv):
        """ Megkeresi, hogy 'number' az 'intv' intervallumban hol van: <i> 
        * Több dimenziós 2 elemes tömbökre! """
        for i, (start,end) in enumerate(intv):
            if start <= number < end:
                return i
        return None

    # Run
    def main(self):
        print(self.resInDataframe())
        print('\nTESZT: ')
        print(self.teszt())
        

if __name__ == "__main__":
    
    # input
    labor = "input_\\labor.csv" 
    techn = "input_\\techn.csv"
    
    # tables
    fajlagos = "tables_\\Fajlagos_T.csv"
    nmax = "tables_\\Nmax_T.csv"
    megosztas = "tables_\\Megosztas_T.csv"
    
    c = SzaktanClass(labor,techn,fajlagos,nmax,megosztas)
    c.main()
    