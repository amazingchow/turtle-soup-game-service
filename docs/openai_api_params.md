

```text
* top_p:

Number between 0 and 1.0. 
An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. 
So 0.1 means only the tokens comprising the top 10% probability mass are considered.

* top_k:

The number of highest probability vocabulary tokens to keep for top-k-filtering. Default value is null, which disables top-k-filtering.
frequency_penalty: 

Number between -2.0 and 2.0. 
Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.

* presence_penalty: 

Number between -2.0 and 2.0.
Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics.

* repetition_penalty: 

Repetition penalty is a technique that penalizes or reduces the probability of generating tokens that have recently appeared in the generated text. 
It encourages the model to generate more diverse and non-repetitive output.
```
