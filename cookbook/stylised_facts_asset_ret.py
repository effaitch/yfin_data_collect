import pandas as pd
import numpy as np
import yfinance as yf
import seaborn as sns
import scipy.stats as scs
import statsmodels.api as sm
import statsmodels.tsa.api as smt

# download data OHLCV
# lower case te column name of close
# calc log return 

"""
1. Non Gaussian distribution of Returns
- negative skewness (3rd momoent)
- excess kurtosis (4th moment)
- how the distribution of returns deviates from normal
- check if the returns vary from nromal quertile 
2. Volatility Clustering
- plot of retunrs show period of significant +ve and -ve returns
- highlight high volatile periods
3. Absence of autocorrelation in returns
- measure similarity to lagged version of timeSeries
- plot shows how many values outside the confidnece interval 
- if the ACF plot is within the 95% confidence interval, then the returns are uncorrelated
4. small and decreasing autocorrelation in squared/abs returns
- to observer small or slowly decaysing autocorrelations
- connected to voaltitliy clustering
- ARCH effect is fn of dquared retn  - elated to GARCH
- investigate by creating acf plots of squared and abs ret
- verify previous acf plot
5. Leverage Effect
- refers that most measures of an asset volatility are negativel correlated with its returns
- to invetigate leverage effect on sp500 retunrs series
6. VIX CBOE Volatility index
- implied by option p[rices on sp50-0 index]
"""
# Normal probability density fn (PDF)
r_range = np.linspace(min(df["log_rtn"]), max(df["log_rtn"]),num=1000)
mu =df["log_rtn"].mean()
sigma=df["log_rtn"].std()
norm_pdf=scs.norm.pdf(r_range,loc=mu,scale=sigma)

#plot histogram and Q-Q plot
fig, ax=plt.subplots(1,2,figsize=(16,8))
#histogram
sns.distplot(df.log_rtn, kde=False,norm_hist=True,ax=ax[0])
ax[0].set_title("Distribution of SP500 returns", fontsize=16)
ax[0].plot(r_range, norm_pdf,"g",lw=2,label=f"N({mu:.2f},{sigma**2:.4f})")
ax[0].legend(loc="upper left")
#Q-Q plot
qq=sm.qqplot(df.log_rtn.values,lines="s",ax=ax[1])
ax[1].set_title("Q-Q plot",fontsize=16)
plt.show()
# can print summaru stat from github repo - need ot check if follows normal distribution

# voaltotoy clusetes
(df["log_rtn"].plot(title="Daily SP500 returns", figsize=(10,6)))

#autocorrelation 
#DEFINE THE PARAMETERS
N_LAGS=50
SIGNIFICANCE_LEVEL=0.05
#ACF= autocrrelation fucntion plot of log ret
acf=smt.graphics.plot_acf(df["log_rtn"],lags=N_LAGS,alpha=SIGNIFICANCE_LEVEL)
plt.show()

# ACF plots squared & abs return
fig, ax=plt.subplots(2,1,figsize=(12,10))
smt.grpahics.plot_acf(df["log_rtn"]**2,lags=N_LAGS,alpha=SIGNIFICANCE_LEVEL,ax=ax[0])
ax[0].set(title="Autocorrelation Plots",ylabel="Swuared Returns")
smt.grpahics.plot_acf(np.abs(df["log_rtn"]),lags=N_LAGS,alpha=SIGNIFICANCE_LEVEL,ax=ax[1])
ax[1].set(ylabel="Absolute Returns",xlabel="lag")
plt.show()

#Leverage effect
#calc colatility measurees as moving std
df["moving_stf_252"]=df[["log_rtn"]].rolling(window=252).std()
df["moving_stf_21"]=df[["log_rtn"]].rolling(window=21).std()
#plot all the series
ig, ax=plt.subplots(3,1,figsize=(18,15),sharex=True)
df["close"].plot(ax=ax[0])
ax[0].set(title="SP500 time series",ylabel="Price($)")
df["log_rtn"].plot(ax=ax[1])
ax[1].set(ylabel="Log returns")
df["rolling_std_252"].plot(ax=ax[2],color="r",label="Rolling Voaltility 252d")
df["rolling_std_21"].plot(ax=ax[2],color="g",label="Rolling Voaltility 21d")
ax[2].set(ylabel="Moving Volatility",xlabel="Date")
ax[2].legend()
plt.show()
#investigate visually comparing price series to rolling volaititly metrics
# shows increased vol when prce decreases and decrese vol when price increases

#VIX CBOE Volatility index
#download data for ^GSPC & ^VIX
df=df["Close"]
df.columns=df.columns.droplevel(0)
df=df.rename(columns={"^GSPC":"sp500","^VIX":"vix"})
#calc log return
df["log_rtn"]=np.log(df["sp500"]/df["sp500"].shift(1))
df["vol_rtn"]=np.log(df["vix"]/df["vix"].shift(1))
df.dropna(how="any",axis=0,inplace=True)
# plot scatter plot & fit reg line
corr_coeff=df.log_rtn.corr(df.vol_rtn)
ax=sns.regplot(x="log_rtn",y="vol_rtn",data=df,line_kws={"color":"red"})
ax.set(title=f"SP500 vs VIX returns($\\rho$={corr_coeff:.2f})",xlabel="SP500 log returns",ylabel="VIX log returns")
plt.show()
