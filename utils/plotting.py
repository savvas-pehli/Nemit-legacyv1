import plotly.express as px
import streamlit as st
import plotly.graph_objects as go
import pandas as pd


def choropleth_mapbox(gdf, geojson, column, region, ani_frame):
    co_max = gdf[column].max()
    pollutant_name, measurement_unit = column.split(" ", 1)
    centralized={"Attica":{"lat":37.98,"lon":23.72}, "Central Macedonia":{"lat":40.629,"lon":22.947}}
    gdf["tooltip_label"] = gdf[column].apply(lambda x: "No data" if x == -1 else f"{x:.4f}")
    pollutant_name=column.split(" ")[0]
    measurement_unit=column.split(" ")[1]
    if ani_frame == 'Hour':
        gdf["tooltip_data"] = gdf.apply(
            lambda row: f"Hour: {row['Hour']}<br>Municipality of {row['municipality']}<br>Air Pollutant: {pollutant_name}<br>Value of air pollutant in {measurement_unit}: {row['tooltip_label']}",
            axis=1)
    else:
        gdf["tooltip_data"] = gdf.apply(
            lambda row: f"Year: {row['Year']}<br>Municipality of {row['municipality']}<br>Air Pollutant: {pollutant_name}<br>Value of air pollutant in {measurement_unit}: {row['tooltip_label']}",
            axis=1)


    fig = px.choropleth_mapbox(
        gdf,
        geojson=geojson,
        color=column,
        animation_frame=ani_frame,
        locations="municipality",
        featureidkey="id",
        mapbox_style="open-street-map",
        color_continuous_scale=[(0, "rgba(128,128,128,0.01)"), (0.01, "blue"), (1, "#006600")],
        zoom=8,
        title=f'Mean concentration of {column.split(" ")[0]} per {ani_frame} <br> for municipalities of {region}',
        center=centralized[region],
        custom_data=['tooltip_data']
    )

    fig.update_traces(hovertemplate="%{customdata[0]}<extra></extra>")
    for f in fig.frames:
        f.data[0].update(hovertemplate="%{customdata[0]}<extra></extra>")

    fig.update_layout(
        coloraxis_colorbar=dict(title=column),
        coloraxis=dict(cmin=0, cmax=co_max),
        geo=dict(showcountries=True, showcoastlines=True, showland=True),
        height=600,
        width=1000,
        title=f"Mean concentration of {pollutant_name} per {ani_frame} in {region}"
    )

    fig.update_traces(marker_line_width=1, marker_line_color='black')
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(height=600, width=1000)
    st.plotly_chart(fig, theme='streamlit', width='stretch')

def dynamic_groupby_bar_chart(df, gases, timeframe):
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
        ]
    month_map = {month: int(index)+1  for index, month in enumerate(months)}
    
    days =['Monday','Tuesday','Wednesday','Thursday','Firday','Saturday','Sunday']
    days_map={day: index+1 for index, day in enumerate(days)}
    fig = go.Figure()
    locations = [name.replace("_", " ") for name in df['Station'].unique()]
    number_of_locations=len(locations)
    gas_info_dict={
         'O3 mug/m^3':'O3 Public level: 180 μg/m3<br>Alarm level: 240 μg/m3<br>Hourly mean values',
         'NO2 mug/m^3':'NO2 Alarm level: 400 μg/m3<br> Hourly mean values',
         'SO2 mug/m^3':'SO2 Alarm level: 500 μg/m3<br> Hourly mean values',
         'CO mg/m^3':'','NO mug/m^3':'','benz mug/m^3':'','PM10 mug/m^3':'','PM2.5 mug/m^3':'','Smoke mg/m^3':''}
    
    stations_num={1:'station',2:'stations',3:'stations'}

    #st.write(stations_num[number_of_locations])
    offsetgroup = 0
    number_of_gases_for_context=len(gases)
    gases_for_context=list(set(gases) & set(gas_info_dict.keys()))
    #st.write(gases)
    for idx, gas in enumerate(gases):
        for station in locations:
            station_data = df[df['Station'] == station]
            if gas in station_data.columns:
                fig.add_trace(go.Bar(
                    x=station_data['record_datetime'],
                    y=station_data[gas],
                    name=f"{station} - {gas}",
                    offsetgroup=str(offsetgroup),
                    yaxis="y" if idx == 0 else "y2"
                )
                              )
            offsetgroup += 1
    
    if not fig.data:
            st.warning("No data traces were added to the plot. Check selected gases, stations, and aggregated data.")
            return
    group_timeframe = {
            "Year": station_data['record_datetime'].sort_values(),
            "Month":station_data['record_datetime'].sort_values().map({v: k for k, v in month_map.items()}).unique(),
            "Day": station_data['record_datetime'].sort_values().map({v: k for k, v in days_map.items()}).unique(),
            "Hour": [f"{int(x):02}:00:00"for x in range(0,24)]
        }

    fig.update_layout(
    xaxis=dict(
    tickmode='array',
    tickvals=station_data['record_datetime'].sort_values(),
    ticktext=tuple(group_timeframe[timeframe])
    )    
        )
    layout_args = {
        "barmode": "group",
        "xaxis": {"title": timeframe},
        "legend_title": "Location - Gas",
        
        "legend": {
        "x": 1.04,  # Right side (0=left, 1=right)
        "y": 1,  # Top (0=bottom, 1=top)
        "xanchor": "left",  # Anchor point for x position
        "yanchor": "top"},
        
        "margin": {"l": 60, "r": 150, "b": 60, "t": 60, "pad": 4},
    }

    if len(gases) == 1:
        layout_args["yaxis"] = {"title": gases[0]}
        layout_args["yaxis"] = {"title": gases[0]}# Single Y-axis case
        layout_args["annotations"] = [
            dict(
            x=0.5,  # Center the text
            y=1.20,  # Slightly above the plot
            xref="paper",
            yref="paper",
            text=f"Pollution Levels of {stations_num[number_of_locations]} {','.join(locations)} <br>for {gases[0].split(' ')[0]} gas",
            showarrow=False,
            font=dict(size=25),
            align="center"
        )
    ]
        if timeframe=='Hour' and number_of_gases_for_context>0:
                context=dict(x=1,  # Center the text
            y=0.5,  # Slightly above the plot
            xref="paper",
            yref="paper",
            xshift=150,
            text=gas_info_dict[gases_for_context[0]],
            showarrow=False,
            font=dict(size=12),
            align="left")
                layout_args['annotations'].append(context)
        layout_args["title"] = ''
    elif len(gases) > 1:
        locations=' , '.join([name.replace("_"," ")for name in locations])
        layout_args["yaxis"] = {"title": gases[0]}
        layout_args["title"]=f"Pollution Levels of {stations_num[number_of_locations]} {locations} for {gases[0]}"
        layout_args["yaxis2"] = {
                     "title": gases[1],
                     "overlaying": "y",  # Overlay on primary y-axis
                     "side": "right",
                     "showgrid": False
                                    }
        layout_args["annotations"] = [
        dict(
            x=0.5,  # Center the text
            y=1.20,  # Slightly above the plot
            xref="paper",
            yref="paper",
            text=f"Pollution Levels of {stations_num[number_of_locations]} {locations} <br>for {', '.join(gases)}",
            showarrow=False,
            font=dict(size=25),
            align="center"
        )]
            
        if timeframe=='Hour' and number_of_gases_for_context>0:
                if number_of_gases_for_context<2:
                    context=dict(x=1,  # Center the text
            y=0.5,  # Slightly above the plot
            xref="paper",
            yref="paper",
            xshift=230,
            text=gas_info_dict[gases_for_context[0]],
            showarrow=False,
            font=dict(size=12),
            align="left")
                elif number_of_gases_for_context>1:
                    context=dict(x=1,  # Center the text
            y=0.5,  # Slightly above the plot
            xref="paper",
            yref="paper",
            xshift=230,
            text=gas_info_dict[gases_for_context[0]]+'<br><br>'+gas_info_dict[gases_for_context[1]],
            showarrow=False,
            font=dict(size=12),
            align="left")
                layout_args['annotations'].append(context)
                    
                    
    
        layout_args["title"] = ''

    fig.update_layout(**layout_args)
    st.plotly_chart(fig, width='stretch')
    
def fuel_con_groupby_bar_chart(df,area,fuels, timeframe='Year'):
    fig = go.Figure()
    locations = list(df[area].unique())
    number_of_locations=len(locations)
    places_num={1:area,2:area+'s',3:area+'s'}

    #st.write(stations_num[number_of_locations])
    offsetgroup = 0
    #fuels_for_context=list(set(fuels) & set(gas_info_dict.keys()))
    #st.write(gases)
    for idx, fuel in enumerate(fuels):
        for place in locations:
            place_data = df[df[area] == place]
            if fuel in place_data.columns:
                fig.add_trace(go.Bar(
                    x=place_data['Year'],
                    y=place_data[fuel],
                    name=f"{place} - {fuel}",
                    offsetgroup=str(offsetgroup),
                    yaxis="y" if idx == 0 else "y2"
                )
                              )
            offsetgroup += 1
    
    if not fig.data:
            st.warning("No data traces were added to the plot. Check selected fuels, {0}s".format(area))
            return
    group_timeframe = {
            "Year": place_data['Year'].sort_values()
        }
    fig.update_layout(
    xaxis=dict(
    tickmode='array',
    tickvals=place_data['Year'].sort_values(),
    ticktext=tuple(place_data['Year'])
    )    
        )
    layout_args = {
        "barmode": "group",
        "xaxis": {"title": timeframe},
        "legend_title": "Location - Gas",
        
        "legend": {
        "x": 1.055,  # Right side (0=left, 1=right)
        "y": 1,  # Top (0=bottom, 1=top)
        "xanchor": "left",  # Anchor point for x position
        "yanchor": "top"},
        
        "margin": {"l": 60, "r": 150, "b": 60, "t": 60, "pad": 4},
    }

    if len(fuels) == 1:
        #layout_args["yaxis"] = {"title": fuels[0]}
        layout_args["yaxis"] = {"title": fuels[0]}# Single Y-axis case
        layout_args["annotations"] = [
            dict(
            x=0.5,  # Center the text
            y=1.20,  # Slightly above the plot
            xref="paper",
            yref="paper",
            text=f"Pollution Levels of {places_num[number_of_locations]} {','.join(locations)} <br>for {fuels[0].split(' ')[0]} fuel",
            showarrow=False,
            font=dict(size=25),
            align="center"
        )
    ]

        layout_args["title"] = ''
    elif len(fuels) > 1:
        locations=' , '.join([name.replace("_"," ")for name in locations])
        layout_args["yaxis"] = {"title": fuels[0]}
        layout_args["title"]=f"Pollution Levels of {places_num[number_of_locations]} {locations} for {fuels[0]}"
        layout_args["yaxis2"] = {
                     "title": fuels[1],
                     "overlaying": "y",  # Overlay on primary y-axis
                     "side": "right",
                     "showgrid": False
                                    }
        layout_args["annotations"] = [
        dict(
            x=0.5,  # Center the text
            y=1.20,  # Slightly above the plot
            xref="paper",
            yref="paper",
            text=f"Pollution Levels of {places_num[number_of_locations]} {locations} <br>for {', '.join(fuels)}",
            showarrow=False,
            font=dict(size=25),
            align="center"
        )]                   
                    
    
        layout_args["title"] = ''

    fig.update_layout(**layout_args)
    st.plotly_chart(fig, width='stretch')
    
def localized_dual_axis_chart(df, y_metrics, timeframe):
    """
    A pure, decoupled bar chart.
    Accepts exactly 1 or 2 metrics and routes them to primary/secondary axes.
    """
    if df is None or df.empty:
        st.warning("No data available to plot.")
        return

    fig = go.Figure()

    # Dynamically assign traces to axes based on the number of metrics
    for idx, metric in enumerate(y_metrics):
        fig.add_trace(go.Bar(
            x=df[timeframe],
            y=df[metric],
            name=metric,
            yaxis="y" if idx == 0 else "y2",
            offsetgroup=str(idx),
            opacity=0.85
        ))

    layout_args = {
        "barmode": "group",
        "xaxis": {
            "title": timeframe, 
            "type": "category" # Forces discrete chronological ordering
        },
        "legend": {
            "x": 1.05, 
            "y": 1, 
            "xanchor": "left", 
            "yanchor": "top"
        },
        "margin": {"l": 60, "r": 60, "b": 60, "t": 60},
        "title": f"Analytics for {', '.join(y_metrics)}"
    }

    # Primary Y-Axis Configuration
    layout_args["yaxis"] = {"title": y_metrics[0]}

    # Secondary Y-Axis Configuration (Only activates if a second metric is passed)
    if len(y_metrics) > 1:
        layout_args["yaxis2"] = {
            "title": y_metrics[1],
            "overlaying": "y",
            "side": "right",
            "showgrid": False
        }

    fig.update_layout(**layout_args)
    
    st.plotly_chart(fig, width='stretch')
    
def plot_particle_distribution(df: pd.DataFrame, measurements: list, timeframe: str):
    """
    Transforms wide-format measurement data and renders a Faceted Line Chart.
    Strictly avoids twin Y-axes by utilizing independent facet rows for vastly different scales.
    """
    if df.empty:
        return None

    # 1. The Transformation (Wide to Long)
    # Plotly Express requires a 'melted' dataframe to map dimensions cleanly.
    # We unpivot the measurement columns into two strictly typed columns: 'Particle_Size' and 'Value'
    df_melted = df.melt(
        id_vars=[timeframe, 'location', 'season'],
        value_vars=measurements,
        var_name='Particle_Size',
        value_name='Concentration'
    )

    # 2. The Figure Architecture
    # We use lines for time-series. 
    # Columns = Locations, Rows = Particle Sizes, Color = Season.
    fig = px.line(
        df_melted,
        x=timeframe,
        y='Concentration',
        color='season',
        facet_col='location',      # Splits places side-by-side
        facet_row='Particle_Size', # Splits measurements top-to-bottom
        markers=True,
        title=f"Particle Concentration Dynamics ({timeframe} Resolution)",
        template="plotly_white",
        hover_data={"location": True, "Particle_Size": True}
    )

    # 3. Scale Optimization
    # If Ch1 has values of 50,000 and Ch2 has values of 0.5, locking the Y-axis 
    # flattens the smaller metric into a straight line. We decouple the row axes.
    fig.update_yaxes(matches=None, showticklabels=True)
    
    # Clean up the subplot titles (Removes the ugly "location=" text Plotly adds by default)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    # Enforce strict X-axis formatting based on the cyclical vs continuous timeframes
    if timeframe == "Hour":
        fig.update_xaxes(
            title_text="Hour of Day",
            tickmode='linear',
            dtick=1, # Forces 24 distinct ticks as you requested
            range=[0, 23]
        )
    elif timeframe == "Day":
        # Let Plotly use the Categorical string names we set in Pandas
        fig.update_xaxes(title_text="Day of the Week")
    else:
        fig.update_xaxes(title_text=timeframe)

    fig.update_layout(
        legend_title_text='Season',
        hovermode="x unified", # Enterprise standard for time-series comparison
        height=300 * len(measurements) # Dynamically scales height based on how many metrics are chosen
    )
    
    fig.for_each_yaxis(lambda y: y.update(title_text='Avg Conc.'))
    
    return fig