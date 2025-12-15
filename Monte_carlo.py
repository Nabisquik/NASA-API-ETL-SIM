import numpy as np 
import matplotlib.pyplot as plt 
import pandas as pd 

# Constants
R_EARTH = 6378.0  # Earth radius in km
V_ESCAPE = 11.2   # Earth escape velocity in km/s

# NASA orbit uncertainty to position uncertainty (Estimated for the simulation- real prob. less scary) 
UNCERTAINTY_MAP = {
    0: 0.01, 1: 0.02, 2: 0.05, 3: 0.10, 4: 0.15,
    5: 0.20, 6: 0.30, 7: 0.40, 8: 0.50, 9: 0.60
}

def impact_simulation(miss_distance_km, velocity_km_s, orbit_uncertainty, n_trials=100000):
    """
    Simple Monte Carlo impact probability calculator
    
    Args:
        miss_distance_km: Miss distance from API
        velocity_km_s: Relative velocity from API
        orbit_uncertainty: Orbit uncertainty (0-9) from API
        n_trials: Number of simulations (default 100k)
    
    Returns:
        Impact probability (0 to 1)
    """
    # Get uncertainty percentage from orbit class
    if isinstance(orbit_uncertainty, str):
        orbit_uncertainty = int(orbit_uncertainty)
    uncertainty = UNCERTAINTY_MAP.get(orbit_uncertainty, 0.10)
 
    # Earth's effective radius with gravitational focusing
    r_critical = R_EARTH * np.sqrt(1 + (V_ESCAPE**2 / velocity_km_s**2))
    
    # Run simulation: sample miss distances
    sigma = miss_distance_km * uncertainty
    sampled_distances = np.random.normal(miss_distance_km, sigma, n_trials)
    impacts = sampled_distances < r_critical
    probability = np.sum(impacts) / n_trials

    # STATS
    # Wilson score interval for binomial proportion
    z = 1.96  
    p_hat = probability
    n = n_trials
    
    denominator = 1 + z**2/n
    center = (p_hat + z**2/(2*n)) / denominator
    margin = z * np.sqrt((p_hat*(1-p_hat)/n + z**2/(4*n**2))) / denominator
    
    ci_lower = max(0, center - margin)
    ci_upper = min(1, center + margin)
    
    std_error = np.sqrt(probability * (1 - probability) / n_trials)
    
    return probability, {
        'sampled_distances': sampled_distances,
        'r_critical': r_critical,
        'impacts': impacts,
        'nominal_miss': miss_distance_km,
        'sigma': sigma,
        'orbit_uncertainty': orbit_uncertainty,
        'uncertainty_percent': uncertainty * 100,
        'confidence_interval_95': (ci_lower, ci_upper),
        'standard_error': std_error,
        'relative_error': std_error / probability if probability > 0 else np.inf
    }

def convergence_analysis(miss_distance_km, velocity_km_s, orbit_uncertainty, 
                         trial_sizes=[1000, 5000, 10000, 50000, 100000]):
    """
    Demonstrate Monte Carlo convergence and optimal sample size
    """
    results = []
    
    for n in trial_sizes:
        prob, _ = impact_simulation(miss_distance_km, velocity_km_s, 
                                    orbit_uncertainty, n_trials=n)
        results.append({'n_trials': n, 'probability': prob})
    
    return pd.DataFrame(results)

def plot_convergence(miss_distance_km, velocity_km_s, orbit_uncertainty,
                     trial_sizes=[1000, 5000, 10000, 50000, 100000, 500000],
                     asteroid_name="Asteroid"):
    """
    Plot convergence analysis showing Monte Carlo stability
    """
    df = convergence_analysis(miss_distance_km, velocity_km_s, orbit_uncertainty, trial_sizes)
    
    plt.style.use('dark_background')
    
    # Dark mode colors
    bg_color = '#1a1a1a'
    panel_color = '#2d2d2d'
    text_color = '#e0e0e0'
    grid_color = '#404040'

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot 1: Probability vs Sample Size
    ax1 = axes[0]
    ax1.plot(df['n_trials'], df['probability'], 'o-', linewidth=2.5, 
             markersize=10, color='#2E86AB', label='Probability Estimate')
    
    final_prob = df['probability'].iloc[-1]
    ax1.axhline(final_prob, color='red', linestyle='--', linewidth=2, alpha=0.6,
                label=f'Converged Value: {final_prob:.2e}')
    
    ax1.set_xscale('log')
    ax1.set_xlabel('Sample Size', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Impact Probability', fontsize=12, fontweight='bold')
    ax1.set_title('Convergence: Probability Estimate vs Sample Size', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3, linestyle='--')
    
    textstr = f'Stabilized at ~{trial_sizes[-2]:,} trials\nFinal: {final_prob:.3e}'
    ax1.text(0.02, 0.98, textstr, transform=ax1.transAxes, 
             fontsize=9, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.6))
    
    # Plot 2: Percent Change from Final Estimate
    ax2 = axes[1]
    final_estimate = df['probability'].iloc[-1]
    percent_diff = ((df['probability'] - final_estimate) / final_estimate * 100).abs()
    
    ax2.plot(df['n_trials'], percent_diff, 'o-', linewidth=2.5, markersize=10, color='#A23B72')
    ax2.axhline(10, color='orange', linestyle='--', linewidth=1.5, label='10% difference', alpha=0.7)
    ax2.axhline(5, color='red', linestyle='--', linewidth=1.5, label='5% difference', alpha=0.7)
    ax2.set_xscale('log')
    ax2.set_yscale('log')
    ax2.set_xlabel('Number of Trials', fontsize=12, fontweight='bold')
    ax2.set_ylabel('|% Difference from Final|', fontsize=12, fontweight='bold')
    ax2.set_title('Convergence Rate: Stability of Estimate', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.legend(fontsize=10)
    
    plt.suptitle(f'Monte Carlo Convergence Analysis: {asteroid_name}\n' +
                 f'Miss: {miss_distance_km:,.0f}km | Velocity: {velocity_km_s:.1f}km/s | Uncertainty: {orbit_uncertainty}',
                 fontsize=13, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    plt.savefig(f'{asteroid_name.replace(" ", "_")}_convergence.png', dpi=150, bbox_inches='tight')
    print(f"Convergence graph saved as: {asteroid_name.replace(' ', '_')}_convergence.png")
    plt.close()
    
    return df


def plot_results3(probability, data, asteroid_name="Asteroid"):
    """Visualization of Monte Carlo results using a vertical-left stack and right-side summary panel"""

    distances = data['sampled_distances']
    r_critical = data['r_critical']
    nominal = data['nominal_miss']
    impacts = data['impacts']
    sigma = data['sigma']

    impact_count = np.sum(impacts)
    miss_count = len(impacts) - impact_count

    plt.style.use('dark_background')
    
    # Dark mode colors
    bg_color = '#1a1a1a'
    panel_color = '#2d2d2d'
    text_color = '#e0e0e0'
    grid_color = '#404040'
    
    fig = plt.figure(figsize=(15, 12), facecolor=bg_color)
    gs = fig.add_gridspec(
        3, 2,
        width_ratios=[2.2, 1],
        height_ratios=[1, 1, 1],
        hspace=0.3,
        wspace=0.15
    )

    axPie   = fig.add_subplot(gs[0, 0], facecolor=bg_color)
    axHist  = fig.add_subplot(gs[1, 0], facecolor=bg_color)
    axScatt = fig.add_subplot(gs[2, 0], facecolor=bg_color)
    axRight = fig.add_subplot(gs[:, 1], facecolor=bg_color)
    axRight.axis('off')

    # PLOT 1 — PIE CHART (Top Left)
    sizes = [impact_count, miss_count]
    labels = [f'IMPACT\n{impact_count:,}', f'MISS\n{miss_count:,}']
    colors = ["#770000", "#0A6D0A"]
    explode = (0.1, 0)

    axPie.pie(
        sizes,
        explode=explode,
        labels=labels,
        colors=colors,
        autopct='%1.4f%%',
        shadow=True,
        startangle=90,
        textprops={'fontsize': 9, 'fontweight': 'bold', 'color': text_color}
    )
    #axPie.set_title("Impact Probability", fontsize=13, fontweight='bold', color=text_color, pad=15)

    # PLOT 2 — HISTOGRAM (MIDDLE LEFT)
    n, bins, patches = axHist.hist(
        distances, bins=60,
        alpha=0.7, edgecolor='white', color='#4a9eff', linewidth=0.5
    )

    # Color bins that fall below the critical radius
    for i, patch in enumerate(patches):
        if bins[i] < r_critical:
            patch.set_facecolor('#ff4444')
            patch.set_alpha(0.8)

    axHist.axvline(
        r_critical, color='#ff6666', linestyle='--', linewidth=2.5,
        label=f'Impact Radius: {r_critical:,.0f} km'
    )
    axHist.axvline(
        nominal, color='#44ff44', linestyle='--', linewidth=2.5,
        label=f'Nominal: {nominal:,.0f} km'
    )
    axHist.axvspan(
        nominal - sigma, nominal + sigma,
        alpha=0.15, color='yellow',
        label=f'Uncertainty ±{sigma:,.0f} km'
    )

    axHist.set_xlabel('Miss Distance (km)', fontsize=12, fontweight='bold', color=text_color)
    axHist.set_ylabel('Frequency', fontsize=12, fontweight='bold', color=text_color)
    axHist.set_title('Miss Distance Distribution', fontsize=13, fontweight='bold', color=text_color, pad=10)
    axHist.legend(fontsize=10, facecolor=panel_color, edgecolor=text_color, framealpha=0.9)
    axHist.grid(True, alpha=0.2, color=grid_color)
    axHist.tick_params(colors=text_color)
    for spine in axHist.spines.values():
        spine.set_edgecolor(text_color)

    # PLOT 3 — SCATTER (BOTTOM LEFT)
    trial_numbers = np.arange(len(distances))
    colors_scatter = ['#ff4444' if imp else '#44ff44' for imp in impacts]

    axScatt.scatter(
        trial_numbers,
        distances,
        c=colors_scatter,
        alpha=0.3,
        s=1
    )
    axScatt.axhline(
        r_critical,
        color='#ff6666',
        linestyle='--',
        linewidth=2,
        label='Impact Threshold'
    )

    axScatt.set_xlabel('Trial Number', fontsize=12, fontweight='bold', color=text_color)
    axScatt.set_ylabel('Miss Distance (km)', fontsize=12, fontweight='bold', color=text_color)
    axScatt.set_title('Individual Simulation Trials', fontsize=13, fontweight='bold', color=text_color, pad=10)
    axScatt.legend(fontsize=10, facecolor=panel_color, edgecolor=text_color, framealpha=0.9)
    axScatt.grid(True, alpha=0.2, color=grid_color)
    axScatt.tick_params(colors=text_color)
    for spine in axScatt.spines.values():
        spine.set_edgecolor(text_color)

    # SUMMARY BOX 
    ci_lower, ci_upper = data['confidence_interval_95']
    # Saftey Margin calc
    closest_sampled = np.min(distances)
    safety_margin = closest_sampled - r_critical
    if safety_margin < 0:
        safety_status = f"X BREACH: {abs(safety_margin):,.0f} km"
    else:
        safety_status = f"✓ Safe: +{safety_margin:,.0f} km"
    
    summary = f"""
    ╔═══════════════════════════════════════╗
    ║        IMPACT SIMULATION RESULTS       ║
    ╚═══════════════════════════════════════╝

    Asteroid: {asteroid_name}

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    IMPACT PROBABILITY
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Chance of Impact:   {probability*100:.6f}%
    Raw Probability:    {probability:.8f}
    
    95% Confidence:     [{ci_lower:.8f}, 
                         {ci_upper:.8f}]
    Standard Error:     {data['standard_error']:.8f}
    
    Impacts:            {impact_count:,} / {len(impacts):,}

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    INPUT DATA
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Nominal Miss:       {nominal:,.0f} km
    Orbit Uncertainty:  {data['orbit_uncertainty']} ({data['uncertainty_percent']:.0f}%)
    Position Sigma:     ±{sigma:,.0f} km

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    EARTH PARAMETERS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Physical Radius:     {R_EARTH:,.0f} km
    Critical Radius:     {r_critical:,.0f} km
    Grav. Focusing:      {r_critical/R_EARTH:.2f}×

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    SIMULATION STATISTICS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Min Distance:   {np.min(distances):,.0f} km
    Max Distance:   {np.max(distances):,.0f} km
    Mean Distance:  {np.mean(distances):,.0f} km
    Median:         {np.median(distances):,.0f} km
    Std Dev:        {np.std(distances):,.0f} km
    
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    MONTE CARLO DETAILS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    Total Trials:       {len(impacts):,}
    Method:             Normal Distribution
    Sampling:           Random (NumPy)
    
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    RISK ASSESSMENT
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    Risk Level:         {'HIGH' if probability > 0.01 else 'MEDIUM' if probability > 0.0001 else 'LOW'}
    Closest Approach:   {closest_sampled:,.0f} km
    Impact Threshold:   {r_critical:,.0f} km
    Safety Margin:      {safety_status}
    """

    # Extends to bottom
    axRight.text(
        0.05, 0.98,
        summary,
        transform=axRight.transAxes,
        fontsize=9.5,
        fontfamily="monospace",
        va="top",
        color=text_color,
        bbox=dict(
            boxstyle="round,pad=0.8", 
            facecolor=panel_color, 
            edgecolor='#666666',
            alpha=0.95,
            linewidth=2
        )
    )

    plt.suptitle(
        f"Monte Carlo Impact Analysis: {asteroid_name}",
        fontsize=26,
        fontweight="bold",
        y=0.995,
        color=text_color
    )

    plt.tight_layout()
    plt.savefig(
        f"{asteroid_name.replace(' ', '_')}_impact_analysis.png",
        dpi=150,
        bbox_inches="tight",
        facecolor=bg_color
    )
    plt.close()
    print(f"Graph saved as: {asteroid_name.replace(' ', '_')}_impact_analysis.png")

if __name__ == "__main__":
    api_ex = pd.read_csv('API_real_data_ex.csv')
    top_df = api_ex.iloc[0, :]

    # Example 1: API top asteroid
    print("="*60)
    print("EXAMPLE 1: Real API asteroid")
    print("="*60)
    
    # Example 1: Real Asteroid Pulled from API
    probability, data = impact_simulation(
        miss_distance_km=top_df['miss_distance_km'],     
        velocity_km_s=top_df['velocity_km_s'],
        orbit_uncertainty=top_df['orbit_uncertainty'],        
        n_trials=500000
    )
    
    print(f"\nImpact Probability: {probability:.8f} ({probability*100:.6f}%)")
    plot_results3(probability, data, f"{top_df['neo_id']} Asteroid")

    # Example 2: Real scary asteroid
    print("="*60)
    print("EXAMPLE 2: Asteroid 99942 Apophis- Expected April 13, 2029")
    print("="*60)
    
    # Example 2: Scary Asteroid from the future
    probability, data = impact_simulation(
        miss_distance_km= 31600,     
        velocity_km_s=7.4,
        orbit_uncertainty=4,        
        n_trials=500000
    )
    
    print(f"\nImpact Probability: {probability:.8f} ({probability*100:.6f}%)")
    plot_results3(probability, data, f"99942 Apophis (Expected 2029)")

    # Generate convergence analysis plot for an assumed terrible case
    print("\nRunning convergence analysis...")
    convergence_df = plot_convergence(
        miss_distance_km= 27500,     
        velocity_km_s=9.2,
        orbit_uncertainty=5,        
        trial_sizes=[100, 1000, 10000, 100000, 500000, 1000000],
        asteroid_name="Fake Asteroid for Impact Data"
    )
    
    print("\nConvergence Results:")
    print(convergence_df.to_string(index=False))
    