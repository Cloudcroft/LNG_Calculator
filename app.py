from flask import Flask, flash, render_template, request, send_from_directory, make_response
import numpy as np
from datetime import datetime
from fpdf import FPDF

###############################################
#          Define flask app                   #
###############################################
app = Flask(__name__) # Creating our Flask Instance
app.secret_key = 'secretKey'

comp = np.zeros(shape=(12,3), dtype=float)
liquid = np.zeros((12,14), dtype=float)
vapor = np.zeros((12,14), dtype=float)
readings = np.zeros((4,2), dtype=float)

###############################################
#  Results array:
#     0,0 - GHV ideal
#     
###############################################
results = np.zeros((1,6), dtype=float)
results[:] = np.nan
# methane, ethane, propane, ibutane, nbutane, ipentane, npentane, hexane, nitrogen (tbd)
# molar hhv (btu/scf)
hvi = np.array([1010.,1769.7,2516.1,3251.9,3262.3,4000.9,4008.7,4755.9,0.,0.,0.])
# molar mass 
mi = np.array([16.0425,30.0690,44.0956,58.1222,58.1222,72.1488,72.1488,86.1754, 28.0134, 31.9988, 44.1010])
# molar mass (btu/lbm)
hmi_imp = np.array([23892.,22334.,21654.,21232.,21300.,21044.,21085.,20943,0.,0.,0.])
hmi_si = np.array([55.575,51.951,50.369,49.388,49.546,48.950,49.045,48.715,0.,0.,0.])
# summation factor
summ = np.array([0.01160, 0.02380, 0.03470, 0.4410, 0.4700, 0.05760, 0.06060, 0.07760, 0.00442, 0.00720, 0.01950])

# the next 3 arrays are per ISO 6578:2017
# molar volume table, Vi (degK / m3/kmol) 
molar_volume = np.array([[106, 108, 110, 112, 114, 116, 118],
                        [0.037234, 0.037481, 0.037735, 0.037995, 0.038262, 0.038536, 0.038817],
                        [0.047348, 0.047512, 0.047678, 0.047845, 0.048014, 0.048184, 0.048356],
                        [0.061855, 0.062033, 0.062212, 0.062392, 0.062574, 0.062756, 0.062939],
                        [0.077637, 0.077836, 0.078035, 0.078236, 0.078438, 0.078640, 0.078844],
                        [0.076194, 0.076384, 0.076574, 0.076765, 0.076957, 0.077150, 0.077344],
                        [0.090948, 0.091163, 0.091379, 0.091596, 0.091814, 0.092032, 0.092251],
                        [0.090833, 0.091042, 0.091252, 0.091462, 0.091673, 0.091884, 0.092095],
                        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                        [0.043002, 0.043963, 0.045031, 0.046231, 0.047602, 0.049179, 0.050885]])

# K1 m3/kmol, degK/MW
k_temp = np.array([105., 110., 115., 120.])
k_mw = np.array([16.0, 17.0, 18.0, 19.0, 20.0])
k1 = np.array([[-0.0070, -0.0080, -0.0090, -0.0100],
              [0.1650, 0.1800, 0.2200, 0.2500],
              [0.3400, 0.3750, 0.4400, 0.5000],
              [0.4750, 0.5350, 0.6100, 0.6950],
              [0.6350, 0.7250, 0.8100, 0.9200]])

k2 = np.array([[-0.100, -0.0150, -0.0240, -0.0320],
              [0.2400, 0.3200, 0.4100, 0.6000],
              [0.4200, 0.5900, 0.7200, 0.9100],
              [0.6100, 0.7700, 0.9500, 1.2300],
              [0.7500, 0.9200, 1.1500, 1.4300]])

paul = dict()
foobar = dict()


@app.route('/', methods=['GET'])
def index():
    comp[:,:] = 0
    liquid[:,:] = 0
    results[:,:] = 0
    readings[:,:] = 0
    flash("Calculation Not Run")
    return render_template('index.html', comp=comp, liquid=liquid, readings=readings)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/pdf')
def show_static_pdf():
    pdf = FPDF(orientation='P', unit='in', format='letter')
    pdf.set_auto_page_break(0)
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(40, 10, 'Good morning SGS!')
    response = make_response(pdf.output(dest='S').encode('latin-1'))
    response.headers.set('Content-Disposition', 'attachment', filename='FLNG-SK-2021-002.pdf')
    response.headers.set('Content-Type', 'application/pdf')
    return response


@app.route('/subscribe')
def subscribe():
    title = "Subscribe to my email newsletter"
    return render_template('subscribe.html', title=title)

@app.route('/form', methods=['POST'])
def form():
    fn = request.form.get('first_name')
    ln = request.form.get('last_name')
    email = request.form.get('email')
    title = "Thank you"

    if not fn or not ln or not email:
        error_statement = "All forms fields required"
        return render_template('subscribe.html', error_statement=error_statement,
                first_name=fn, last_name=ln)

    subscribers.append(f'{fn} {ln} | {email}')
    return render_template('form.html', title=title, subscribers=subscribers)

###############################################
#            LNG Calculation                  #
###############################################
@app.route('/operation_result/', methods=['POST'])
def operation_result():
    title = "LNG Calculator"

    error = None
    result = None

    # request.form looks for:
    # html tags with matching "name= "
    
    form_data_dict  = request.form.to_dict()
    print(form_data_dict)
   
    
    comp[0,0] = request.form.get('C1_input')
    comp[1,0] = request.form.get('C2_input') 
    comp[2,0] = request.form.get('C3_input')  
    comp[3,0] = request.form.get('iC4_input')  
    comp[4,0] = request.form.get('nC4_input')  
    comp[5,0] = request.form.get('iC5_input')  
    comp[6,0] = request.form.get('nC5_input')  
    comp[7,0] = request.form.get('C6_input') 
    comp[8,0] = request.form.get('N2_input') 
    comp[9,0] = 0
    comp[10,0] = 0 

    readings[0,0] = form_data_dict['vapor_temp_before']
    readings[1,0] = form_data_dict['vapor_pres_before']
    readings[2,0] = form_data_dict['liq_temp_before'] 
    readings[3,0] = form_data_dict['liq_vol_before']
    readings[0,1] = form_data_dict['vapor_temp_after']
    readings[1,1] = form_data_dict['vapor_pres_after']
    readings[2,1] = form_data_dict['liq_temp_after']
    readings[3,1] = form_data_dict['liq_vol_after']

    normalization = request.form.get('normalization') 
    print("***********************", normalization)

    try:

        form_data_dict['vapor_temp_before'] = float(form_data_dict['vapor_temp_before'])
        form_data_dict['vapor_temp_after'] = float(form_data_dict['vapor_temp_after']) 
        form_data_dict['vapor_pres_before'] = float(form_data_dict['vapor_pres_before']) 
        form_data_dict['vapor_pres_after'] = float(form_data_dict['vapor_pres_after']) 
        form_data_dict['liq_temp_before']  = float(form_data_dict['liq_temp_before']) 
        form_data_dict['liq_temp_after'] = float(form_data_dict['liq_temp_after']) 
        form_data_dict['liq_vol_before'] = float(form_data_dict['liq_vol_before']) 
        form_data_dict['liq_vol_after'] = float(form_data_dict['liq_vol_after'])   
        form_data_dict['liq_vol_net'] = form_data_dict['liq_vol_after'] - form_data_dict['liq_vol_before'] 

        print(form_data_dict)

###############################################
#  Initialize 'liquid' array with input       #
###############################################
        liquid[0,0] = float(comp[0,0])
        liquid[1,0]= float(comp[1,0])
        liquid[2,0]= float(comp[2,0])
        liquid[3,0]= float(comp[3,0])
        liquid[4,0]= float(comp[4,0])
        liquid[5,0]= float(comp[5,0])
        liquid[6,0]= float(comp[6,0])
        liquid[7,0]= float(comp[7,0])
        liquid[8,0]= float(comp[8,0])
        liquid[9,0]= 0.
        liquid[10,0]= 0.
        liquid[11,0] = np.sum(liquid[:10,0])

         # On default, the operation on webpage is addition
        if normalization == "methane":
            liquid[:,1] = liquid[:,0]
            liquid[0,1] = (100.0 - liquid[11,0]) + liquid[0,0]
            liquid[:,2] = liquid[:,1]/100.
            liquid[11,1] = np.sum(liquid[:10,1])
            liquid[11,2] = np.sum(liquid[:10,2])


        if normalization == "proportional":
            print("proprtional")
            liquid[:,1] = liquid[:,0]
            diff = 100.0 - liquid[11,0]
            liquid[:,1] = liquid[:,0]/liquid[11,0] * diff + liquid[:,0]
            liquid[11,1] = np.sum(liquid[:10,1])
            liquid[:,2] = liquid[:,1] / 100.

        if liquid[0,1] > 100. or liquid[0,1] < 0. :
            flash("Measured LNG values cannot be normalized. Check inputs and rerun.")

        print("==================================")
        print("Normalize comp (Col 1")
        print(liquid[:,1])
        print("==================================")

        print("==================================")
        print("Normalize mol frac (Col 2")
        print(liquid[:,2])
        print("==================================")

###############################################
#      Calculate normalization and mol frac   #
###############################################        
#        liquid[:10, 1] = liquid[:10, 0]
#        liquid[0, 1] = (100.0 - liquid[11, 0]) + liquid[0, 0]
#        liquid[:10, 2] = liquid[:10, 1]/100.
#        liquid[11, 1] = np.sum(liquid[:10, 1])
#        liquid[11, 2] = np.sum(liquid[:10, 2])

###############################################
#      Initialize with standard values        #
###############################################  
        liquid[:10,3] = mi[:10]

        print("==================================")
        print("MW (Col 3)")
        print(liquid[:,3])
        print("==================================")

        liquid[:10,4] = liquid[:10,2] * liquid[:10,3]
        liquid[11,4] = np.sum(liquid[:10,4])

        print("==================================")
        print("Xi x Mi (Col 4)")
        print(liquid[:,4])
        print("==================================")

###############################################
#      Calculate molar volumes                #
###############################################  
        liqtemp_degC = form_data_dict['liq_temp_after']  # for testing
        liqtemp_degK = liqtemp_degC + 273.15
        
        liquid[0,5] = round(np.interp(liqtemp_degK, molar_volume[0,:], molar_volume[1,:]),6)
        liquid[1,5] = round(np.interp(liqtemp_degK, molar_volume[0,:], molar_volume[2,:]),6)
        liquid[2,5] = round(np.interp(liqtemp_degK, molar_volume[0,:], molar_volume[3,:]),6)
        liquid[3,5] = round(np.interp(liqtemp_degK, molar_volume[0,:], molar_volume[4,:]),6)
        liquid[4,5] = round(np.interp(liqtemp_degK, molar_volume[0,:], molar_volume[5,:]),6)
        liquid[5,5] = round(np.interp(liqtemp_degK, molar_volume[0,:], molar_volume[6,:]),6)
        liquid[6,5] = round(np.interp(liqtemp_degK, molar_volume[0,:], molar_volume[7,:]),6)
        liquid[7,5] = round(np.interp(liqtemp_degK, molar_volume[0,:], molar_volume[8,:]),6)
        liquid[8,5] = round(np.interp(liqtemp_degK, molar_volume[0,:], molar_volume[9,:]),6)
        liquid[9,5] = 0.
        liquid[10,5] = 0.

        print("==================================")
        print("Vi (Col 5)")
        print(liquid[:,5])
        print("==================================")

###############################################
#      Calculate xi * vi (Column 6)           #
###############################################  
        liquid[:10,6] = liquid[:10,2] * liquid[:10,5] 
        liquid[11,6] = np.sum(liquid[:10,6])
        print("==================================")
        print("Molar Volumes (Col 6)")
        print(liquid[:,6])
        print("==================================")

        liquid[:10,7] = hmi_imp[:10]
        print("==================================")
        print("BTU/lbm (Col 7)")
        print(liquid[:,7])
        print("==================================")

        liquid[:10,8] = hmi_si[:10]
        print("==================================")
        print("MJ/kg (Col 8)")
        print(liquid[:,8])
        print("==================================")

        liquid[:10,9] = liquid[:10,2] * liquid[:10,3] * liquid[:10,7]
        liquid[11,9] = np.sum(liquid[:10,9])
        print("==================================")
        print("Xi x Mi x Hmi (Col 9)")
        print(liquid[:,9])
        print("==================================")

        liquid[:10,10] = hvi[:10]
        print("==================================")
        print("Hvi (Col 10)")
        print(liquid[:,10])
        print("==================================")

        liquid[:10,11] = liquid[:10,2] * liquid[:10,10]
        liquid[11,11] = np.sum(liquid[:10,11])
        print("==================================")
        print("Xi x Hvi (Col 11)")
        print(liquid[:,11])
        print("==================================")

        liquid[:10,12] = summ[:10]
        print("==================================")
        print("sqrt(b) (Col 12)")
        print(liquid[:,12])
        print("==================================")

        liquid[:10,13] = liquid[:10,2] * liquid[:10,12]
        liquid[11,13] = 1 - pow(np.sum(liquid[:10,13]),2)*14.696
        print("==================================")
        print("Xi x sqrt(b) (Col 13)")
        print(liquid[:,13])
        print("==================================")

        form_data_dict['ghv_ideal'] = liquid[11,11]  
        form_data_dict['mw'] = liquid[11,4]  
        form_data_dict['xi_vi'] = liquid[11,6]  
        form_data_dict['xi_mi_hmi'] = liquid[11,9]  
        form_data_dict['z'] = liquid[11,13]  
        form_data_dict['ghv_real'] = liquid[11,11]/liquid[11,13] 
        
        k_pop = np.zeros((5,1), dtype=float)
        k_pop[0,0] = np.interp(form_data_dict['liq_temp_after'] + 273.15, k_temp, k1[0,:])
        k_pop[1,0] = np.interp(form_data_dict['liq_temp_after'] + 273.15, k_temp, k1[1,:])
        k_pop[2,0] = np.interp(form_data_dict['liq_temp_after'] + 273.15, k_temp, k1[2,:])
        k_pop[3,0] = np.interp(form_data_dict['liq_temp_after'] + 273.15, k_temp, k1[3,:])
        k_pop[4,0] = np.interp(form_data_dict['liq_temp_after'] + 273.15, k_temp, k1[4,:])
        form_data_dict['k1'] = round(np.interp(form_data_dict['mw'], k_mw, k_pop[:,0])/1000.,6)

        k_pop[0,0] = np.interp(form_data_dict['liq_temp_after'] + 273.15, k_temp, k2[0,:])
        k_pop[1,0] = np.interp(form_data_dict['liq_temp_after'] + 273.15, k_temp, k2[1,:])
        k_pop[2,0] = np.interp(form_data_dict['liq_temp_after'] + 273.15, k_temp, k2[2,:])
        k_pop[3,0] = np.interp(form_data_dict['liq_temp_after'] + 273.15, k_temp, k2[3,:])
        k_pop[4,0] = np.interp(form_data_dict['liq_temp_after'] + 273.15, k_temp, k2[4,:])
        form_data_dict['k2'] = round(np.interp(form_data_dict['mw'], k_mw, k_pop[:,0])/1000.,6)

        print(form_data_dict['liq_temp_after'] + 273.15,)
        print(k_temp[:])
        print(k2[1,:], k_pop[:,0])


        form_data_dict['c'] = form_data_dict['k1'] + ((form_data_dict['k2'] - form_data_dict['k1']) * liquid[0,2]/0.0425)
        form_data_dict['density'] = round(form_data_dict['mw']/(form_data_dict['xi_vi']-(form_data_dict['c']*1)),2)
        form_data_dict['hm_btu'] = round(form_data_dict['xi_mi_hmi']/form_data_dict['mw']*2.20462,2)
        form_data_dict['hm_mj'] = np.sum(liquid[:10,4]*liquid[:10,8]) / form_data_dict['mw']
        form_data_dict['e_gross'] = form_data_dict['liq_vol_net'] * form_data_dict['density'] * form_data_dict['hm_btu'] * 1e-6
        form_data_dict['e_net'] = 0. 
        
        results[0,0] = liquid[11,11]                          # GHV ideal       results[0,2] = liquid[11,4]                           # molar mass
        results[0,3] = liquid[11,6]                           # Xi x Vi
        results[0,4] = liquid[11,9]                           # Xi x Mi x Hmi
        results[0,5] = liquid[11,13]                          # compressibilty
        results[0,1] = liquid[11,11]/liquid[11,13]            # GHV real

        print("==================================")
        print("Dictionary")
        print(form_data_dict['hm_mj'])
        print("==================================")

# On default, the operation on webpage is addition

        return render_template(
            'index.html',
            comp=comp,
            normalization=normalization,
            results=results,
            liquid=liquid,
            foobar=form_data_dict,
            readings=readings,
            datetime=datetime.utcnow().strftime('%A %m-%d-%Y, %H:%M:%S'),
            calculation_success=True
        )
        
    except ZeroDivisionError:
        return render_template(
            'index.html',
            comp=comp,
            liquid=liquid,
            operation=normalization,
            readings=readings,
            result="Bad Input Zero",
            calculation_success=False,
            error="You cannot divide by zero"
        )
        
    except ValueError:
        return render_template(
            'index.html',
            comp=comp,
            liquid=liquid,
            operation=normalization,
            result="Bad Input value",
            calculation_success=False,
            error="Cannot perform numeric operations with provided input"
        )

if __name__ == '__main__':
    app.run(debug=True)
