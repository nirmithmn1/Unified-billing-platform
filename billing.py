class BillingEngine:
    @staticmethod
    def calculate_package_cost(trip_count, billing_model):
        base_cost = billing_model['base_cost']
        if trip_count <= billing_model['trip_limit']:
            return base_cost
        extra_trips = trip_count - billing_model['trip_limit']
        return base_cost + (extra_trips * billing_model['extra_rate_per_trip'])

    @staticmethod
    def calculate_trip_cost(distance_km, duration_hours, billing_model):
        return (distance_km * billing_model['rate_per_km']) + \
               (duration_hours * billing_model['rate_per_hour'])

    @staticmethod
    def calculate_hybrid_cost(trip_count, distance_km, duration_hours, billing_model):
        base_cost = billing_model['base_cost']
        trip_cost = (distance_km * billing_model['rate_per_km']) + \
                   (duration_hours * billing_model['rate_per_hour'])
        return base_cost + trip_cost

    @classmethod
    def calculate_cost(cls, trip_data, billing_model):
        if billing_model['type'] == 'package':
            return cls.calculate_package_cost(trip_data['trip_count'], billing_model)
        elif billing_model['type'] == 'trip':
            return cls.calculate_trip_cost(
                trip_data['distance_km'], 
                trip_data['duration_hours'], 
                billing_model
            )
        elif billing_model['type'] == 'hybrid':
            return cls.calculate_hybrid_cost(
                trip_data['trip_count'],
                trip_data['distance_km'],
                trip_data['duration_hours'],
                billing_model
            )
        return 0