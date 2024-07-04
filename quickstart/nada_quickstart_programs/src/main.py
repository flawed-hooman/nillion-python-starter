from nada_dsl import *

def nada_main():
    nr_parties = 2
    p0_points = 10
    p1_points = 10
    precision = 5
    total_points = p0_points + p1_points
    parties = []
    for i in range(nr_parties):
        parties.append(Party(name="Party" + str(i)))
    outparty = Party(name="OutParty")

    xi_vector = []
    yi_vector = []
    for i in range(p0_points):
        xi_vector.append(SecretInteger(Input(name="x" + str(i), party=parties[0])))
        yi_vector.append(SecretInteger(Input(name="y" + str(i), party=parties[0])))
    for i in range(p1_points):
        xi_vector.append(
            SecretInteger(Input(name="x" + str(i + p0_points), party=parties[1]))
        )
        yi_vector.append(
            SecretInteger(Input(name="y" + str(i + p0_points), party=parties[1]))
        )

    sum_x = xi_vector[0]
    sum_y = yi_vector[0]
    sum_xy = xi_vector[0] * yi_vector[0]
    sum_xx = xi_vector[0] * xi_vector[0]
    sum_yy = yi_vector[0] * yi_vector[0]
    for i in range(1, total_points):
        sum_x += xi_vector[i]
        sum_y += yi_vector[i]
        sum_xy += xi_vector[i] * yi_vector[i]
        sum_xx += xi_vector[i] * xi_vector[i]
        sum_yy += yi_vector[i] * yi_vector[i]

    n = Integer(total_points)
    n_times_sum_xy = n * sum_xy
    sum_x_times_sum_y = sum_x * sum_y
    ld = n * sum_xx - sum_x * sum_x
    rd = n * sum_yy - sum_y * sum_y

    numerator = n_times_sum_xy - sum_x_times_sum_y
    denominator = ld * rd
    sq_numerator = numerator * numerator * Integer(10**precision)
    r2 = sq_numerator / denominator
    sign = n_times_sum_xy > sum_x_times_sum_y

    return [
        (Output(r2, "correlation_coefficient_squared", outparty)),
        (Output(sign, "sign", outparty)),
    ]