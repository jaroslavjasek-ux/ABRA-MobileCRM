using Microsoft.Extensions.DependencyInjection;

namespace MobileCrm.Adapter.Gen;

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddGenIntegration(this IServiceCollection services)
    {
        services.AddScoped<IRepresentativeService, RepresentativeService>();
        services.AddScoped<IMyDayService, MyDayService>();
        services.AddScoped<IFirmService, FirmService>();
        services.AddScoped<IContactService, ContactService>();
        services.AddScoped<IActivityService, ActivityService>();
        services.AddScoped<IActivityCreateService, ActivityCreateService>();
        services.AddScoped<IReferenceDefaultsService, ReferenceDefaultsService>();
        services.AddScoped<IUserLookupService, UserLookupService>();
        return services;
    }
}
