from datetime import datetime

class Formatter:
    
    @staticmethod
    def date_time_to_timestamp(date_time: str):
        # 1. Converte a string para um objeto datetime
        # %Y = ano, %m = mês, %d = dia, %H = hora, %M = minuto
        dt = datetime.strptime(date_time, "%Y-%m-%d %H:%M")
        # Transforma em timestamp inteiro (segundos)
        return int(dt.timestamp())

    @staticmethod
    def str_price_to_float(price: str):
        try:
            if not price:
                return 0.0
            # "1,879 €" -> 1.879
            return float(str(price).replace("€", "").replace(",", ".").strip())
        except (ValueError, TypeError):
            return 0.0
