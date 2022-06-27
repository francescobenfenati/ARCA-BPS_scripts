/usr/bin/python /home/km3net/applications/bps-test/benfe_jsendcommand.py
sleep 1
FILENAME="/home/km3net/applications/bps-test/csv_bps"/*
echo Copied $FILENAME
sleep 1
/usr/bin/python3 /home/km3net/applications/bps-test/csv-to-influxdb_UTC_RP.py --dbname bps_monitoring --create --user km3net --password pyrosoma --server 172.16.65.46:8087 --input $FILENAME --tagcolumns source --fieldcolumns bps_5V_max_current,bps_5V_max_current_A,lbl_max_current,lbl_max_current_A,bps_du_max_current,bps_du_max_current_A,bps_du_max_return_current,bps_du_max_return_current_A,bps_V_max,bps_V_max_V,bps_hydro_I_max,bps_hydro_I_max_A,bps_mon_max_temp_heatsink,bps_mon_max_temp_heatsink_AU,bps_mon_max_temp_board,bps_mon_max_temp_board_C,bps_5V_mean_current,bps_5V_mean_current_A,lbl_mean_current,lbl_mean_current_A,bps_du_mean_current,bps_du_mean_current_A,bps_du_mean_return_current,bps_du_mean_return_current_A,bps_V_mean,bps_V_mean_V,bps_hydro_mean_current,bps_hydro_mean_current_A,bps_mon_mean_temp_heatsink,bps_mon_mean_temp_heatsink_AU,bps_mon_mean_temp_board,bps_mon_mean_temp_board_C -tc machine_time -tf "%Y-%m-%d %H:%M:%S" --timezone Europe/Rome
sleep 1
rm -f $FILENAME
echo Removed csv
