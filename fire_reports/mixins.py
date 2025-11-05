class VehicleStatusFieldsMixin:
    """میکسین برای مدیریت فیلدهای وضعیت خودرو"""
    
    @staticmethod
    def get_status_fields():
        """لیست فیلدهای وضعیت را برمی‌گرداند"""
        return [
            'horn_status',
            'hose_status',
            'monitor_status',
            'extinguisher_status',
            'equipment_status',
            'foam_status',
            'water_status',
            'tire_status',
            'brake_status',
            'lighting_status'
        ]

    def get_status_descriptions(self, instance):
        """توضیحات مربوط به وضعیت‌های نامناسب را برمی‌گرداند"""
        descriptions = {}
        for field in self.get_status_fields():
            base_name = field.replace('_status', '')
            desc_field = f'{base_name}_description'
            if hasattr(instance, desc_field):
                descriptions[field] = getattr(instance, desc_field)
        return descriptions

    def get_vehicle_status_context(self, instance):
        """دیکشنری شامل وضعیت‌ها و توضیحات را برمی‌گرداند"""
        status_fields = {}
        for field in self.get_status_fields():
            if hasattr(instance, field):
                status_fields[field] = getattr(instance, field)
        
        return {
            'status_fields': status_fields,
            'descriptions': self.get_status_descriptions(instance)
        }